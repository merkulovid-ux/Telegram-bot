import importlib
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_config_has_required_values():
    config = importlib.import_module("config")
    assert config.TELEGRAM_BOT_TOKEN
    assert config.DATABASE_URL
    assert config.YANDEX_API_KEY
    assert config.YANDEX_FOLDER_ID
