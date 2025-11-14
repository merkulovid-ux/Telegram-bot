import os
from dotenv import load_dotenv

load_dotenv()


def _require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Не найдена обязательная переменная окружения {name}")
    return value


TELEGRAM_BOT_TOKEN = _require("TELEGRAM_BOT_TOKEN")

YANDEX_API_KEY = _require("YANDEX_API_KEY")
YANDEX_FOLDER_ID = _require("YANDEX_FOLDER_ID")

# Параметры для ассистента AI Studio
YC_API_KEY = os.getenv("YC_API_KEY") or YANDEX_API_KEY
YC_FOLDER_ID = os.getenv("YC_FOLDER_ID") or YANDEX_FOLDER_ID
YC_SEARCH_INDEX_ID = os.getenv("YC_SEARCH_INDEX_ID")
YC_ASSISTANT_ID = os.getenv("YC_ASSISTANT_ID")
YC_ASSISTANT_MODEL_URI = os.getenv("YC_ASSISTANT_MODEL_URI")

MANAGED_RAG_PUBLIC_URL = os.getenv("MANAGED_RAG_PUBLIC_URL")
MANAGED_RAG_TOKEN = os.getenv("MANAGED_RAG_TOKEN")
MANAGED_RAG_VERSION_ID = os.getenv("MANAGED_RAG_VERSION_ID")
MANAGED_RAG_MODEL = os.getenv("MANAGED_RAG_MODEL", "t-tech/T-lite-it-1.0")

DATABASE_URL = _require("DATABASE_URL")
