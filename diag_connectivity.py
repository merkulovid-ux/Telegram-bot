import asyncio
import json
import os
import time
from typing import Dict, Optional

import asyncpg

from kb_metadata import get_kb_structure
from config import DATABASE_URL

try:
    import boto3
except Exception:
    boto3 = None


def log_result(component: str, status: str, message: str, extra: Optional[Dict] = None):
    """Выводит результат проверки в консоль и в JSON (для Cloud Logging)."""
    payload = {
        "component": component,
        "status": status,
        "message": message,
    }
    if extra:
        payload.update(extra)
    print(json.dumps(payload))


async def test_db() -> bool:
    started = time.time()
    try:
        conn = await asyncpg.connect(dsn=DATABASE_URL)
        val = await conn.fetchval("SELECT 1")
        await conn.close()
        log_result(
            "postgresql",
            "OK",
            f"SELECT 1 -> {val}",
            {"duration_ms": int((time.time() - started) * 1000)},
        )
        return True
    except Exception as exc:
        log_result(
            "postgresql",
            "FAILED",
            str(exc),
            {"duration_ms": int((time.time() - started) * 1000)},
        )
        return False


async def test_search_index() -> bool:
    started = time.time()
    try:
        data = await get_kb_structure(force_refresh=True)
        topics = {item.name: len(item.topics) for item in data} if data else {}
        log_result(
            "search_index",
            "OK" if data else "EMPTY",
            "Search index loaded",
            {
                "categories": len(data) if data else 0,
                "topics": topics,
                "duration_ms": int((time.time() - started) * 1000),
            },
        )
        return bool(data)
    except Exception as exc:
        log_result(
            "search_index",
            "FAILED",
            str(exc),
            {"duration_ms": int((time.time() - started) * 1000)},
        )
        return False


def test_object_storage() -> bool:
    started = time.time()
    bucket = os.getenv("YC_OBS_BUCKET")
    access_key = os.getenv("YC_OBS_ACCESS_KEY_ID")
    secret_key = os.getenv("YC_OBS_SECRET_ACCESS_KEY")
    endpoint = os.getenv("YC_OBS_ENDPOINT", "https://storage.yandexcloud.net")
    region = os.getenv("YC_OBS_REGION", "ru-central1")

    if not bucket or not access_key or not secret_key:
        log_result(
            "object_storage",
            "SKIPPED",
            "Credentials not fully configured",
            {"duration_ms": int((time.time() - started) * 1000)},
        )
        return True

    if boto3 is None:
        log_result(
            "object_storage",
            "SKIPPED",
            "boto3 not installed",
            {"duration_ms": int((time.time() - started) * 1000)},
        )
        return True

    try:
        s3 = boto3.client(
            "s3",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            endpoint_url=endpoint,
            region_name=region,
        )
        response = s3.list_objects_v2(Bucket=bucket, MaxKeys=5)
        contents = response.get("Contents", [])
        log_result(
            "object_storage",
            "OK" if contents else "EMPTY",
            f"Bucket {bucket}",
            {
                "objects": [
                    {"key": obj["Key"], "size": obj["Size"]}
                    for obj in contents
                ],
                "duration_ms": int((time.time() - started) * 1000),
            },
        )
        return True
    except Exception as exc:
        log_result(
            "object_storage",
            "FAILED",
            str(exc),
            {"duration_ms": int((time.time() - started) * 1000)},
        )
        return False


async def main() -> int:
    db_ok = await test_db()
    search_ok = await test_search_index()
    obs_ok = test_object_storage()
    all_ok = db_ok and search_ok and obs_ok
    log_result("summary", "OK" if all_ok else "FAILED", "Diagnostics finished")
    return 0 if all_ok else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    raise SystemExit(exit_code)
