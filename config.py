import os
from dotenv import load_dotenv

load_dotenv()


def _require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Environment variable required: {name}")
    return value


# Core required settings (Cloud.ru VM)
TELEGRAM_BOT_TOKEN = _require("TELEGRAM_BOT_TOKEN")
DATABASE_URL = _require("DATABASE_URL")
ADMIN_ID = int(_require("ADMIN_ID"))


# Cloud.ru auth (for GigaChat or other services)
CLOUDRU_CLIENT_ID = os.getenv("CLOUDRU_CLIENT_ID")
CLOUDRU_CLIENT_SECRET = os.getenv("CLOUDRU_CLIENT_SECRET")
CLOUDRU_TOKEN = os.getenv("CLOUDRU_TOKEN")

