from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Iterable, List

from cloudru_client import GigaChatClient


@dataclass(frozen=True)
class AssistantResponse:
    text: str
    thread_id: str | None
    run_id: str | None
    citations: tuple[str, ...]
    usage: object | None


_CLIENT: GigaChatClient | None = None


def _get_client() -> GigaChatClient:
    global _CLIENT  # pylint: disable=global-statement
    if _CLIENT is None:
        _CLIENT = GigaChatClient()
    return _CLIENT


def _normalize_messages(messages: Iterable[dict[str, str] | str]) -> List[str]:
    prepared: List[str] = []
    for raw in messages:
        if isinstance(raw, str):
            prepared.append(raw)
            continue
        text = raw.get("content") or raw.get("text")
        if text:
            prepared.append(text)
    if not prepared:
        raise ValueError("Нет сообщений для ассистента")
    return prepared


def _run_sync(messages: Iterable[dict[str, str] | str]) -> AssistantResponse:
    client = _get_client()
    normalized = _normalize_messages(messages)
    prompt = "\n".join(normalized)
    result = asyncio.run(client.generate_text(prompt))

    text = result.get("content") or ""
    return AssistantResponse(
        text=text,
        thread_id=None,
        run_id=None,
        citations=tuple(),
        usage=result.get("usage"),
    )


async def run_assistant(
    messages: Iterable[dict[str, str] | str],
    *,
    thread_id: str | None = None,  # kept for compatibility, unused
) -> AssistantResponse:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _run_sync, messages)


def format_citations(citations: tuple[str, ...]) -> str:
    return ""
