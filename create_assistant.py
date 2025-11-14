import os
from pathlib import Path

from dotenv import load_dotenv

from yandex_cloud_ml_sdk import YCloudML  # type: ignore
from yandex_cloud_ml_sdk._tools.search_index.tool import SearchIndexTool  # type: ignore


def env(name: str) -> str | None:
    value = os.getenv(name)
    return value.strip() if value else None


def read_fallback(path: str) -> str:
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Не найден файл {path} с идентификатором.")
    return file_path.read_text(encoding="utf-8").strip()


def main() -> None:
    load_dotenv()

    folder_id = env("YC_FOLDER_ID") or env("YANDEX_FOLDER_ID")
    api_key = env("YC_API_KEY") or env("YANDEX_API_KEY")
    if not folder_id or not api_key:
        raise RuntimeError("Задайте YC_FOLDER_ID и YC_API_KEY в .env.")

    search_index_id = env("YC_SEARCH_INDEX_ID") or read_fallback(".yc_search_index_id")

    sdk = YCloudML(folder_id=folder_id, auth=api_key)

    name = env("YC_ASSISTANT_NAME") or "processoff-rag-helper"
    model_uri = env("YC_ASSISTANT_MODEL_URI") or f"gpt://{folder_id}/yandexgpt-lite"
    instruction = env("YC_ASSISTANT_INSTRUCTION") or (
        "Ты — AI-помощник команды ProcessOff. Отвечай по-деловому, но дружелюбно, и опирайся "
        "только на предоставленный контекст из базы знаний (Search Index). Если ответа нет в "
        "контенте, честно сообщай об этом. В конце коротко предлагай следующий шаг."
    )

    tool = SearchIndexTool(search_index_ids=(search_index_id,), max_num_results=6)

    assistant = sdk.assistants.create(
        model=model_uri,
        name=name,
        instruction=instruction,
        tools=[tool],
        labels={"project": "telegram-ai-bot", "env": "dev"},
    )

    print(f"Assistant created: id={assistant.id}, name={assistant.name}")
    Path(".yc_assistant_id").write_text(assistant.id, encoding="utf-8")
    print("ID ассистента сохранён в .yc_assistant_id")


if __name__ == "__main__":
    main()

