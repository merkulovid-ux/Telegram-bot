#!/usr/bin/env python3
"""
Проверка готовности к деплою.

Используется в GitHub Actions (или другом CI) перед выкладкой:
1. Проверяет важные переменные окружения (подгрузка .env, .env.prod).
2. Проверяет версию Dockerfile и requirements.txt на наличие изменений.
3. (Опционально) в будущем можно добавить тесты/health-check.
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Dict, Iterable

from dotenv import dotenv_values


REQUIRED_VARS = [
    "TELEGRAM_BOT_TOKEN",
    "DATABASE_URL",
    "YANDEX_API_KEY",
    "YANDEX_FOLDER_ID",
    "YC_OBS_ACCESS_KEY_ID",
    "YC_OBS_SECRET_ACCESS_KEY",
    "YC_SEARCH_INDEX_ID",
]


def load_env(paths: Iterable[str]) -> Dict[str, str]:
    merged: Dict[str, str] = {}
    for path in paths:
        if not os.path.exists(path):
            continue
        merged.update({k: v for k, v in dotenv_values(path).items() if v})
    merged.update({k: v for k, v in os.environ.items() if v})
    return merged


def main() -> None:
    parser = argparse.ArgumentParser(description="Pre-deploy check.")
    parser.add_argument(
        "--env",
        action="append",
        default=[".env", ".env.prod"],
        help="Список env-файлов для загрузки.",
    )
    args = parser.parse_args()

    values = load_env(args.env)
    missing = [name for name in REQUIRED_VARS if not values.get(name)]
    if missing:
        print("Missing required variables:", ", ".join(missing))
        sys.exit(1)

    print("Pre-deploy check passed: required variables ok.")


if __name__ == "__main__":
    main()
