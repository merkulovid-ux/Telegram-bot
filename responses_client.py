from __future__ import annotations

import io
import logging
import re
from pathlib import Path
from typing import Iterable, List, Tuple

from pypdf import PdfReader  # type: ignore

from cloudru_client import GigaChatClient

logger = logging.getLogger(__name__)

KB_DIR = Path("data_pdfs/knowledge_base")
_KB_CACHE: dict[str, tuple[str, str]] = {}
_CLIENT: GigaChatClient | None = None


def _get_client() -> GigaChatClient:
    global _CLIENT  # pylint: disable=global-statement
    if _CLIENT is None:
        _CLIENT = GigaChatClient()
    return _CLIENT


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
    if not KB_DIR.exists():
        logger.warning("Knowledge base directory not found: %s", KB_DIR)
        return
    for file_path in KB_DIR.rglob("*"):
        if not file_path.is_file():
            continue
        suffix = file_path.suffix.lower()
        try:
            if suffix == ".pdf":
                text = _extract_text_from_pdf_bytes(file_path.read_bytes())
            elif suffix in {".txt", ".md"}:
                text = _normalize_text(file_path.read_text(encoding="utf-8", errors="ignore"))
            else:
                continue
            if text:
                _KB_CACHE[str(file_path)] = (file_path.name, text)
        except Exception as exc:
            logger.warning("Failed to load %s: %s", file_path, exc)


def _split_chunks(text: str, *, size: int = 900, overlap: int = 150) -> List[str]:
    chunks: List[str] = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = max(0, end - overlap)
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
    context = "\n\n".join(chunks)
    template = {
        "ask": "You are a helpful assistant for ProcessOff. Answer based on provided context and suggest next step.",
        "swot": "You are a strategic consultant. Provide SWOT analysis (Strengths, Weaknesses, Opportunities, Threats).",
        "digest": "Summarize the topic into 3-5 bullet points for a teammate.",
        "nvc": "Rephrase the phrase in the Nonviolent Communication format (Observation-Feeling-Need-Request).",
        "po_helper": "Assist a Product Owner: explain, give example, and recommend the next step.",
        "mediate": "Act as a mediator for a team conflict; structure the answer clearly.",
    }
    system = template.get(mode, template["ask"])
    return (
        system
        + "\n\nContext:\n"
        + context
        + "\n\nQuestion: "
        + query
        + "\n\nAnswer:"
    )


async def _call_model(prompt: str) -> str:
    client = _get_client()
    result = await client.generate_text(prompt)
    return (result.get("content") or "").strip()


async def generate_rag_answer(query: str) -> tuple[str, List[str]]:
    chunks, titles = _retrieve_top_chunks(query, top_k=5)
    prompt = _build_prompt(chunks, query, mode="ask")
    return await _call_model(prompt), titles


async def generate_rag_swot(query: str) -> tuple[str, List[str]]:
    chunks, titles = _retrieve_top_chunks(query, top_k=6)
    prompt = _build_prompt(chunks, query, mode="swot")
    return await _call_model(prompt), titles


async def generate_rag_digest(query: str) -> tuple[str, List[str]]:
    chunks, titles = _retrieve_top_chunks(query, top_k=6)
    prompt = _build_prompt(chunks, query, mode="digest")
    return await _call_model(prompt), titles


async def generate_rag_nvc(query: str) -> tuple[str, List[str]]:
    chunks, titles = _retrieve_top_chunks(query, top_k=5)
    prompt = _build_prompt(chunks, query, mode="nvc")
    return await _call_model(prompt), titles


async def generate_rag_po_helper(query: str) -> tuple[str, List[str]]:
    chunks, titles = _retrieve_top_chunks(query, top_k=5)
    prompt = _build_prompt(chunks, query, mode="po_helper")
    return await _call_model(prompt), titles


async def generate_rag_conflict(query: str) -> tuple[str, List[str]]:
    chunks, titles = _retrieve_top_chunks(query, top_k=6)
    prompt = _build_prompt(chunks, query, mode="mediate")
    return await _call_model(prompt), titles
