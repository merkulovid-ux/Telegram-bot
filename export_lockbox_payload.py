#!/usr/bin/env python3
"""
Генератор payload для Yandex Lockbox.

Пример:
    python export_lockbox_payload.py --env .env --env .env.prod --output secrets.json
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Dict, Iterable, List

from dotenv import dotenv_values

DEFAULT_KEYS = [
    "TELEGRAM_BOT_TOKEN",
    "YC_API_KEY",
    "YANDEX_API_KEY",
    "YC_OBS_ACCESS_KEY_ID",
    "YC_OBS_SECRET_ACCESS_KEY",
    "YC_OBS_BUCKET",
    "YC_OBS_PREFIX",
    "DATABASE_URL",
    "YC_SEARCH_INDEX_ID",
    "YC_ASSISTANT_ID",
]


def load_env(paths: Iterable[str]) -> Dict[str, str]:
    merged: Dict[str, str] = {}
    for path in paths:
        if not path:
            continue
        file = Path(path)
        if not file.exists():
            continue
        merged.update({k: v for k, v in dotenv_values(str(file)).items() if v})
    merged.update({k: v for k, v in os.environ.items() if v})
    return merged


def main() -> None:
    parser = argparse.ArgumentParser(description="Экспорт значений из .env в Lockbox payload.")
    parser.add_argument("--env", action="append", default=[".env"], help="Пути к .env файлам")
    parser.add_argument("--output", default="secrets.json", help="Файл для сохранения payload")
    parser.add_argument(
        "--keys",
        nargs="+",
        default=DEFAULT_KEYS,
        help="Ключи для экспорта (по умолчанию TELEGRAM_BOT_TOKEN, YC_* и т.д.)",
    )
    args = parser.parse_args()

    values = load_env(args.env)
    entries: List[Dict[str, str]] = []
    missing: List[str] = []
    for key in args.keys:
        value = values.get(key)
        if value is None:
            missing.append(key)
            continue
        entries.append({"key": key, "textValue": value})

    payload = {"entries": entries}
    Path(args.output).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Payload written to {args.output} ({len(entries)} entries).")
    if missing:
        print("Missing keys (not exported):", ", ".join(missing))


if __name__ == "__main__":
    main()
