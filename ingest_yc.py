import os
import sys
import time
from pathlib import Path
from typing import Iterable

from dotenv import load_dotenv
from pypdf import PdfReader  # type: ignore

try:
    import boto3  # type: ignore
except Exception:  # pragma: no cover
    boto3 = None

from yandex_cloud_ml_sdk import YCloudML  # type: ignore
from yandex_cloud_ml_sdk.search_indexes import VectorSearchIndexType  # type: ignore


def print_step(msg: str) -> None:
    print(f"[ingest-yc] {msg}")


def env(name: str, default: str | None = None) -> str | None:
    return os.getenv(name, default)


def discover_local_files(root: Path, exts: Iterable[str] = (".pdf", ".txt", ".md")) -> list[Path]:
    files: list[Path] = []
    if not root.exists():
        return files
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in exts:
            files.append(path)
    return files


def extract_category_topic(file_path: Path) -> tuple[str, str]:
    """
    Пытаемся понять категорию и тему из текста первой страницы.
    Если не получилось — fallback к имени файла.
    """
    try:
        reader = PdfReader(str(file_path))
        text = reader.pages[0].extract_text() if reader.pages else ""
    except Exception:
        text = ""

    normalized = text.lower()
    if "scrum" in normalized:
        category = "Scrum"
    elif "коуч" in normalized or "coaching" in normalized:
        category = "Coaching"
    elif "agile" in normalized:
        category = "Agile"
    else:
        category = "Общее"

    # Возьмём первые ~8 слов текста в качестве темы
    words = text.strip().split()
    topic_text = " ".join(words[:8]) if words else file_path.stem
    topic = topic_text.replace("\n", " ").strip() or file_path.name

    return category, topic[:150]


def infer_labels(file_path: Path) -> dict[str, str]:
    category, topic = extract_category_topic(file_path)
    return {
        "source": file_path.name,
        "kb_category": category[:100],
        "kb_topic": topic,
    }


def upload_to_object_storage(files: list[Path], base_dir: Path) -> None:
    bucket = env("YC_OBS_BUCKET")
    if not bucket:
        print_step("YC_OBS_BUCKET не задан — пропускаю загрузку в Object Storage")
        return

    if boto3 is None:
        print_step("boto3 недоступен — пропускаю загрузку в Object Storage")
        return

    access_key = env("YC_OBS_ACCESS_KEY_ID")
    secret_key = env("YC_OBS_SECRET_ACCESS_KEY")
    endpoint = env("YC_OBS_ENDPOINT", "https://storage.yandexcloud.net")
    region = env("YC_OBS_REGION", "ru-central1")
    prefix = env("YC_OBS_PREFIX", "knowledge-base/")

    if not access_key or not secret_key:
        print_step("Нет статических ключей для Object Storage — пропускаю загрузку")
        return

    s3 = boto3.client(
        "s3",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        endpoint_url=endpoint,
        region_name=region,
    )

    uploaded = 0
    for file_path in files:
        relative = file_path.relative_to(base_dir)
        key = prefix + "/".join(relative.parts)
        s3.upload_file(str(file_path), bucket, key)
        uploaded += 1
        print_step(f"Загружен в S3: s3://{bucket}/{key}")

    print_step(f"Всего загружено в Object Storage: {uploaded} файлов")


def create_search_index_with_sdk(files: list[Path], base_dir: Path) -> str:
    folder_id = env("YC_FOLDER_ID") or env("YANDEX_FOLDER_ID")
    api_key = env("YC_API_KEY") or env("YANDEX_API_KEY")
    if not folder_id or not api_key:
        raise RuntimeError("YC_FOLDER_ID/YC_API_KEY не заданы в окружении")

    sdk = YCloudML(folder_id=folder_id, auth=api_key)

    uploaded_files = []
    for file_path in files:
        labels = infer_labels(file_path)
        print_step(
            f"Загружаю файл в AI Studio: {file_path.name} "
            f"(категория: {labels['kb_category']}, тема: {labels['kb_topic']})"
        )
        yc_file = sdk.files.upload(
            file_path,
            ttl_days=30,
            expiration_policy="static",
            name=file_path.name,
            labels=labels,
        )
        uploaded_files.append(yc_file)

    ts = time.strftime("%Y%m%d-%H%M%S")
    idx_name = f"kb-{ts}"
    print_step("Создаю поисковый индекс (VectorSearchIndexType)")
    operation = sdk.search_indexes.create_deferred(
        uploaded_files,
        index_type=VectorSearchIndexType(),
        name=idx_name,
        labels={"project": "telegram-ai-bot", "purpose": "kb"},
    )
    search_index = operation.wait()
    print_step(f"Индекс готов: id={search_index.id}, name={idx_name}")
    return search_index.id


def main() -> None:
    load_dotenv()

    base_dir = Path(__file__).parent / "data_pdfs"
    files = discover_local_files(base_dir)
    if not files:
        print_step("В data_pdfs нет подходящих файлов (.pdf/.txt/.md)")
        sys.exit(0)

    upload_to_object_storage(files, base_dir)
    idx_id = create_search_index_with_sdk(files, base_dir)

    Path(".yc_search_index_id").write_text(idx_id, encoding="utf-8")
    print_step(f"ID индекса записан в .yc_search_index_id ({idx_id})")


if __name__ == "__main__":
    main()
