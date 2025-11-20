#!/usr/bin/env python3
"""
Проверка переменных окружения для Telegram AI Bot.

Скрипт помогает виртуальной команде быстро понять, какие ключи
подготовлены (локально или в Secrets Manager), а какие ещё нужно
создать, прежде чем деплоить решение в инфраструктуру Yandex Cloud.
"""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple

from dotenv import dotenv_values


@dataclass
class VarSpec:
    name: str
    description: str
    required: bool = True


CATEGORIES: Dict[str, List[VarSpec]] = {
    "Telegram": [
        VarSpec("TELEGRAM_BOT_TOKEN", "Токен BotFather для основного бота"),
    ],
    "Database": [
        VarSpec("DATABASE_URL", "Строка подключения к PostgreSQL (локально или Managed)"),
    ],
    "Yandex Core": [
        VarSpec("YANDEX_API_KEY", "API-ключ сервисного аккаунта (ai.assistants.editor)"),
        VarSpec("YANDEX_FOLDER_ID", "Каталог, в котором создаются ассистенты"),
        VarSpec("YC_API_KEY", "Альтернативный API-ключ (используется SDK)", required=False),
        VarSpec("YC_FOLDER_ID", "Альтернативный folder_id (если отличается)", required=False),
    ],
    "Object Storage": [
        VarSpec("YC_OBS_ACCESS_KEY_ID", "Access Key для Object Storage"),
        VarSpec("YC_OBS_SECRET_ACCESS_KEY", "Secret Key для Object Storage"),
        VarSpec("YC_OBS_BUCKET", "Бакет с базой знаний"),
        VarSpec("YC_OBS_PREFIX", "Префикс каталога (обычно knowledge-base/)", required=False),
        VarSpec("YC_OBS_ENDPOINT", "Endpoint (https://storage.yandexcloud.net)", required=False),
        VarSpec("YC_OBS_REGION", "Регион (ru-central1)", required=False),
    ],
    "RAG / Search Index": [
        VarSpec("YC_SEARCH_INDEX_ID", "ID поискового индекса (создаётся ingest_yc.py)", required=False),
        VarSpec("YC_ASSISTANT_ID", "ID ассистента (create_assistant.py)", required=False),
        VarSpec("YC_ASSISTANT_MODEL_URI", "URI модели ассистента", required=False),
        VarSpec("YC_ASSISTANT_INSTRUCTION", "Инструкция ассистента", required=False),
    ],
    "Managed RAG (Responses API)": [
        VarSpec("MANAGED_RAG_PUBLIC_URL", "publicUrl Managed RAG", required=False),
        VarSpec("MANAGED_RAG_VERSION_ID", "ID версии RAG", required=False),
        VarSpec("MANAGED_RAG_TOKEN", "Токен доступа к Responses API", required=False),
        VarSpec("MANAGED_RAG_MODEL", "URI модели для retrieve_generate", required=False),
    ],
}


def load_env(paths: Iterable[str]) -> Dict[str, str]:
    """Собираем значения из переданных файлов и переменных окружения."""
    merged: Dict[str, str] = {}
    for path in paths:
        if not path:
            continue
        if not os.path.exists(path):
            continue
        merged.update({k: v for k, v in dotenv_values(path).items() if v is not None})
    merged.update({k: v for k, v in os.environ.items() if v})
    return merged


def render_table(rows: List[Tuple[str, str, str]]) -> str:
    widths = [
        max(len(row[0]) for row in rows),
        max(len(row[1]) for row in rows),
        max(len(row[2]) for row in rows),
    ]
    lines = []
    for row in rows:
        padded = [
            row[0].ljust(widths[0]),
            row[1].ljust(widths[1]),
            row[2].ljust(widths[2]),
        ]
        lines.append(" | ".join(padded))
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Проверяет необходимые переменные окружения для Telegram AI Bot."
    )
    parser.add_argument(
        "--env",
        action="append",
        default=[".env", ".env.local", ".env.prod"],
        help="Путь к .env файлу (можно указать несколько, по умолчанию .env, .env.local, .env.prod).",
    )
    args = parser.parse_args()

    values = load_env(args.env)

    overall_missing = 0
    for category, specs in CATEGORIES.items():
        rows: List[Tuple[str, str, str]] = []
        missing_required = 0
        for spec in specs:
            value = values.get(spec.name)
            status = "OK" if value else ("—" if spec.required else "optional")
            if spec.required and not value:
                overall_missing += 1
                missing_required += 1
            rows.append((spec.name, status, spec.description))

        print(f"\n[{category}]")
        print(render_table(rows))
        if missing_required:
            print(f"[! ] Требуется заполнить {missing_required} критичных значений.")
        else:
            print("[OK] Критичные значения заполнены.")

    if overall_missing:
        print(
            f"\nИтог: не заполнено {overall_missing} обязательных переменных. "
            "Создайте/обновите секреты в Yandex Cloud или .env файлы."
        )
        raise SystemExit(1)

    print("\nИтог: все обязательные переменные присутствуют. Можно продолжать деплой.")


if __name__ == "__main__":
    main()
