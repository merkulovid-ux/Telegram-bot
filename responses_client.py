from __future__ import annotations

import httpx
import io
import logging
import re
from typing import Iterable, List, Tuple

from pypdf import PdfReader  # type: ignore

from assistant_client import get_sdk, get_search_index
from config import (
    MANAGED_RAG_MODEL,
    MANAGED_RAG_PUBLIC_URL,
    MANAGED_RAG_TOKEN,
    MANAGED_RAG_VERSION_ID,
    YC_ASSISTANT_MODEL_URI,
    YC_FOLDER_ID,
)

logger = logging.getLogger(__name__)


_KB_CACHE: dict[str, tuple[str, str]] = {}

_SYSTEM_PROMPTS: dict[str, str] = {
    "ask": (
        "Вы помогающий ассистент ProcessOff. Отвечайте по контексту, подсказывая следующий шаг "
        "для Product Owner, Scrum Master или команды."
    ),
    "digest": "Сформируй 3-5 заметных тезисов по теме так, как если бы писал дайджест для команды.",
    "swot": "Проанализируй ситуацию по SWOT (Strengths, Weaknesses, Opportunities, Threats).",
    "nvc": (
        "Перефразируй запрос в стиле ненасильственного общения (наблюдение, чувство, потребность, просьба)."
    ),
    "po_helper": (
        "Объясни, какие действия должен совершить Product Owner, приведи пример и предложи следующий шаг."
    ),
    "mediate": (
        "Ты медиатор и коуч для Scrum-команд. Собирай контекст, задавай уточняющие вопросы и помогай "
        "построить путь к разрешению конфликта."
    ),
}


def _managed_rag_enabled() -> bool:
    return bool(MANAGED_RAG_PUBLIC_URL and MANAGED_RAG_TOKEN and MANAGED_RAG_VERSION_ID)


def _build_managed_payload(query: str, prompt: str, *, retrieve_limit: int, n_chunks: int) -> dict:
    return {
        "query": query,
        "rag_version": MANAGED_RAG_VERSION_ID,
        "retrieve_limit": retrieve_limit,
        "n_chunks_in_context": n_chunks,
        "llm_settings": {
            "model_settings": {"model": MANAGED_RAG_MODEL},
            "system_prompt": prompt,
        },
    }


def _extract_managed_text_fragment(fragment: object) -> str:
    if isinstance(fragment, str):
        return fragment.strip()
    if isinstance(fragment, dict):
        for key in ("text", "answer", "content", "generation", "message"):
            value = fragment.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        if "candidates" in fragment and isinstance(fragment["candidates"], list):
            for candidate in fragment["candidates"]:
                text = _extract_managed_text_fragment(candidate)
                if text:
                    return text
    if isinstance(fragment, list):
        for value in fragment:
            text = _extract_managed_text_fragment(value)
            if text:
                return text
    return ""


def _extract_managed_text(response: dict) -> str:
    text = _extract_managed_text_fragment(response.get("result"))
    if text:
        return text
    if "items" in response and isinstance(response["items"], list):
        for item in response["items"]:
            text = _extract_managed_text_fragment(item.get("result") or item)
            if text:
                return text
    return _extract_managed_text_fragment(response)


def _call_managed_rag(
    query: str,
    mode: str,
    *,
    retrieve_limit: int,
    n_chunks: int,
) -> str:
    if not _managed_rag_enabled():
        return ""

    prompt = _SYSTEM_PROMPTS.get(mode, _SYSTEM_PROMPTS["ask"])
    payload = _build_managed_payload(query, prompt, retrieve_limit=retrieve_limit, n_chunks=n_chunks)
    endpoint = MANAGED_RAG_PUBLIC_URL.rstrip("/")

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{endpoint}/api/v1/retrieve_generate",
                json=payload,
                headers={
                    "Authorization": f"Bearer {MANAGED_RAG_TOKEN}",
                    "Content-Type": "application/json",
                },
            )
            response.raise_for_status()
            return _extract_managed_text(response.json())
    except httpx.HTTPError as exc:
        logger.warning("Managed RAG request failed; falling back to local model: %s", exc)
        return ""


def _maybe_managed_rag(query: str, mode: str, *, retrieve_limit: int, n_chunks: int) -> str | None:
    text = _call_managed_rag(query, mode, retrieve_limit=retrieve_limit, n_chunks=n_chunks)
    return text or None


def _normalize_text(text: str) -> str:
    text = text.replace("\x00", " ")
    return re.sub(r"\s+", " ", text).strip()


def _extract_text_from_pdf_bytes(data: bytes, *, max_pages: int = 30) -> str:
    with io.BytesIO(data) as bio:
        reader = PdfReader(bio)
        pages = min(len(reader.pages), max_pages)
        parts: List[str] = []
        for i in range(pages):
            try:
                parts.append(reader.pages[i].extract_text() or "")
            except Exception:
                continue
        return _normalize_text("\n".join(parts))


def _load_kb_cache() -> None:
    if _KB_CACHE:
        return
    sdk = get_sdk()
    index = get_search_index()
    for idx_file in index.list_files():
        try:
            file_obj = sdk.files.get(idx_file.id)
            name = file_obj.name or idx_file.id
            data = file_obj.download_as_bytes(timeout=60)
            if name.lower().endswith(".pdf"):
                text = _extract_text_from_pdf_bytes(data)
            else:
                try:
                    text = data.decode("utf-8", errors="ignore")
                except Exception:
                    text = ""
            text = _normalize_text(text)
            if text:
                _KB_CACHE[idx_file.id] = (name, text)
        except Exception:
            continue


def _split_chunks(text: str, *, size: int = 900, overlap: int = 150) -> List[str]:
    chunks: List[str] = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = end - overlap
        if start < 0:
            start = 0
    return chunks


def _score_chunk(query: str, chunk: str) -> int:
    tokens = re.findall(r"\w+", query.lower())
    if not tokens:
        return 0
    lower = chunk.lower()
    return sum(lower.count(token) for token in tokens)


def _retrieve_top_chunks(query: str, *, top_k: int) -> Tuple[List[str], List[str]]:
    _load_kb_cache()
    scored: List[tuple[int, str, str]] = []
    for title, text in _KB_CACHE.values():
        for chunk in _split_chunks(text):
            score = _score_chunk(query, chunk)
            if score > 0:
                scored.append((score, chunk, title))
    if not scored:
        return [], []
    scored.sort(key=lambda item: item[0], reverse=True)
    top = scored[:top_k]
    return [chunk for _, chunk, _ in top], list(dict.fromkeys([title for _, _, title in top]))


def _build_prompt(chunks: Iterable[str], query: str, *, mode: str) -> str:
    context = "\\n\\n".join(chunks)
    template = {
        "ask": "You are the ProcessOff helper. Answer based on provided context and suggest the next step.",
        "swot": "You are a strategic consultant. Provide SWOT analysis (Strengths, Weaknesses, Opportunities, Threats).",
        "digest": "Summarize the topic into 3-5 bullet points for a teammate.",
        "nvc": "Rephrase the phrase in the Nonviolent Communication format (Observation-Feeling-Need-Request).",
        "po_helper": "Assist a Product Owner: explain, give example, and recommend the next step.",
        "mediate": (
            "Ты эксперт-медиатор. Сначала выясни роли, позиции и потребности сторон, уточни контекст "
            "и эмоции, затем предложи пути диалога и возможные шаги. Обязательно задавай уточняющие вопросы, "
            "если недостаточно информации, и проси пользователя описать, что именно произошло."
        ),
    }
    system = template.get(mode, template["ask"])
    return (
        system
        + "\\n\\nContext:\\n"
        + context
        + "\\n\\nQuestion: "
        + query
        + "\\n\\nAnswer:"
    )


def _call_model(prompt: str) -> str:
    sdk = get_sdk()
    model_uri = YC_ASSISTANT_MODEL_URI or f"gpt://{YC_FOLDER_ID}/yandexgpt-lite"
    model = sdk.models.completions(model_uri)
    result = model.run(prompt)
    return (result.text or "").strip()


def generate_rag_answer(query: str) -> tuple[str, List[str]]:
    managed = _maybe_managed_rag(query, "ask", retrieve_limit=3, n_chunks=3)
    if managed:
        return managed, []

    chunks, titles = _retrieve_top_chunks(query, top_k=5)
    prompt = _build_prompt(chunks, query, mode="ask")
    return _call_model(prompt), titles


def generate_rag_swot(query: str) -> tuple[str, List[str]]:
    managed = _maybe_managed_rag(query, "swot", retrieve_limit=4, n_chunks=3)
    if managed:
        return managed, []

    chunks, titles = _retrieve_top_chunks(query, top_k=6)
    prompt = _build_prompt(chunks, query, mode="swot")
    return _call_model(prompt), titles


def generate_rag_digest(query: str) -> tuple[str, List[str]]:
    managed = _maybe_managed_rag(query, "digest", retrieve_limit=4, n_chunks=3)
    if managed:
        return managed, []

    chunks, titles = _retrieve_top_chunks(query, top_k=6)
    prompt = _build_prompt(chunks, query, mode="digest")
    return _call_model(prompt), titles


def generate_rag_nvc(query: str) -> tuple[str, List[str]]:
    managed = _maybe_managed_rag(query, "nvc", retrieve_limit=3, n_chunks=3)
    if managed:
        return managed, []

    chunks, titles = _retrieve_top_chunks(query, top_k=5)
    prompt = _build_prompt(chunks, query, mode="nvc")
    return _call_model(prompt), titles


def generate_rag_po_helper(query: str) -> tuple[str, List[str]]:
    managed = _maybe_managed_rag(query, "po_helper", retrieve_limit=3, n_chunks=3)
    if managed:
        return managed, []

    chunks, titles = _retrieve_top_chunks(query, top_k=5)
    prompt = _build_prompt(chunks, query, mode="po_helper")
    return _call_model(prompt), titles
def generate_rag_conflict(query: str) -> tuple[str, List[str]]:
    managed = _maybe_managed_rag(query, "mediate", retrieve_limit=5, n_chunks=3)
    if managed:
        return managed, []

    chunks, titles = _retrieve_top_chunks(query, top_k=6)
    prompt = _build_prompt(chunks, query, mode="mediate")
    return _call_model(prompt), titles
