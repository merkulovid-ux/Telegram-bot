from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Iterable

from yandex_cloud_ml_sdk import YCloudML
from yandex_cloud_ml_sdk._messages.citations import Citation, FileChunk
from yandex_cloud_ml_sdk._runs.run import RunResult
from yandex_cloud_ml_sdk._types.message import TextMessageDict

from config import YC_API_KEY, YC_ASSISTANT_ID, YC_FOLDER_ID, YC_SEARCH_INDEX_ID


@dataclass(frozen=True)
class AssistantResponse:
    text: str
    thread_id: str
    run_id: str
    citations: tuple[Citation, ...]
    usage: object | None


_SDK: YCloudML | None = None
_ASSISTANT = None


def _require(name: str, value: str | None) -> str:
    if not value:
        raise ValueError(f"Не найдена обязательная переменная окружения {name}")
    return value


def get_sdk() -> YCloudML:
    global _SDK  # pylint: disable=global-statement
    if _SDK is None:
        folder_id = _require("YC_FOLDER_ID", YC_FOLDER_ID)
        api_key = _require("YC_API_KEY", YC_API_KEY)
        _SDK = YCloudML(folder_id=folder_id, auth=api_key)
    return _SDK


def get_assistant():
    global _ASSISTANT  # pylint: disable=global-statement
    if _ASSISTANT is None:
        assistant_id = _require("YC_ASSISTANT_ID", YC_ASSISTANT_ID)
        _ASSISTANT = get_sdk().assistants.get(assistant_id)
    return _ASSISTANT


def get_search_index():
    search_index_id = _require("YC_SEARCH_INDEX_ID", YC_SEARCH_INDEX_ID)
    return get_sdk().search_indexes.get(search_index_id)


def _normalize_messages(messages: Iterable[dict[str, str] | str]) -> list[TextMessageDict]:
    prepared: list[TextMessageDict] = []
    for raw in messages:
        if isinstance(raw, str):
            prepared.append({"role": "user", "text": raw})
            continue

        text = raw.get("content") or raw.get("text")
        if not text:
            continue
        role = raw.get("role") or "user"
        prepared.append({"role": role, "text": text})

    if not prepared:
        raise ValueError("Список сообщений пуст — нечего отправлять ассистенту")
    return prepared


def _run_sync(messages: Iterable[dict[str, str] | str], thread_id: str | None) -> AssistantResponse:
    sdk = get_sdk()
    assistant = get_assistant()
    normalized = _normalize_messages(messages)

    thread = sdk.threads.get(thread_id) if thread_id else sdk.threads.create()
    for msg in normalized:
        thread.write(msg)

    run = assistant.run(thread)
    result: RunResult[object] = run.result()
    return AssistantResponse(
        text=result.text or "",
        thread_id=thread.id,
        run_id=run.id,
        citations=tuple(result.citations),
        usage=result.usage,
    )


async def run_assistant(
    messages: Iterable[dict[str, str] | str],
    *,
    thread_id: str | None = None,
) -> AssistantResponse:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _run_sync, messages, thread_id)


def format_citations(citations: tuple[Citation, ...]) -> str:
    titles: list[str] = []
    for citation in citations:
        for source in citation.sources:
            name = _extract_source_name(source)
            if name and name not in titles:
                titles.append(name)
    if not titles:
        return ""

    shown = titles[:5]
    suffix = "" if len(titles) <= 5 else "\n…и другие источники."
    lines = "\n".join(f"• {title}" for title in shown)
    return f"Источники:\n{lines}{suffix}"


def _extract_source_name(source: object) -> str | None:
    if isinstance(source, FileChunk):
        if source.file and getattr(source.file, "name", None):
            return source.file.name
        if source.search_index and getattr(source.search_index, "name", None):
            return source.search_index.name
    source_type = getattr(source, "type", None)
    return source_type if isinstance(source_type, str) else None
