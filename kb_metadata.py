from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Dict, List

from assistant_client import get_sdk, get_search_index
from config import YC_SEARCH_INDEX_ID

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CategoryTopics:
    name: str
    topics: List[str]


_CACHE: List[CategoryTopics] = []
_CACHE_TIMESTAMP = 0.0
_CACHE_LOCK = asyncio.Lock()
_CACHE_TTL_SECONDS = 0


async def get_kb_structure(force_refresh: bool = False) -> List[CategoryTopics]:
    """
    Возвращает список категорий и тем, извлечённых из файлов Search Index.
    Результат кэшируется, чтобы не дергать API каждый раз.
    """
    global _CACHE, _CACHE_TIMESTAMP  # pylint: disable=global-statement

    if not YC_SEARCH_INDEX_ID:
        return []

    needs_refresh = (
        not _CACHE
        or force_refresh
        or (time.time() - _CACHE_TIMESTAMP) > _CACHE_TTL_SECONDS
    )

    if needs_refresh:
        async with _CACHE_LOCK:
            needs_refresh = (
                not _CACHE
                or force_refresh
                or (time.time() - _CACHE_TIMESTAMP) > _CACHE_TTL_SECONDS
            )
            if needs_refresh:
                logger.info("Refreshing KB categories from Search Index %s", YC_SEARCH_INDEX_ID)
                _CACHE = await asyncio.to_thread(_load_structure)
                _CACHE_TIMESTAMP = time.time()

    return _CACHE


def _load_structure() -> List[CategoryTopics]:
    sdk = get_sdk()
    try:
        search_index = get_search_index()
    except Exception as exc:  # noqa: BLE001
        logger.error("Не удалось получить Search Index: %s", exc)
        return []

    categories: Dict[str, set[str]] = {}

    def _extract_category(labels: dict | None) -> str:
        labels = labels or {}
        return labels.get("kb_category") or labels.get("category") or "Общее"

    def _extract_topic(labels: dict | None, fallback: str) -> str:
        labels = labels or {}
        return labels.get("kb_topic") or labels.get("title") or fallback

    for idx_file in search_index.list_files():
        try:
            file_obj = sdk.files.get(idx_file.id)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Не удалось получить информацию о файле %s: %s", idx_file.id, exc)
            continue

        labels = getattr(file_obj, "labels", {}) or {}
        category = _extract_category(labels)
        topic = _extract_topic(labels, file_obj.name or f"Файл {idx_file.id}")
        categories.setdefault(category, set()).add(topic)

    structured: List[CategoryTopics] = []
    for cat in sorted(categories):
        topics = sorted(categories[cat])
        structured.append(CategoryTopics(name=cat, topics=topics))
    return structured
