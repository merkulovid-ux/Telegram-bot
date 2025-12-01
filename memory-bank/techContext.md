# Tech Context

- Language/runtime: Python 3.11.
- Frameworks/libs: Aiogram, LangGraph, langchain-core messages, asyncpg, httpx, pypdf.
- External services: Cloud.ru VM; managed RAG from Cloud.ru is not connected; **no Yandex usage** (code still has Yandex deps that must be removed/replaced).
- Config: `.env` with TELEGRAM_BOT_TOKEN, DATABASE_URL, ADMIN_ID; Yandex/Managed RAG vars should be dropped when code is refactored off Yandex.
- CI/CD: `.github/workflows/terraform-cloudru-v10.yml`; docs for Cloud.ru in `docs/infra/SBERCLOUD_*`, `docs/cloudru_kb/*`, `docs/infra/CICD_GUIDE.md`.
- Tests/checks: `pytest tests/test_smoke.py`; `check_env.py`; `diag_connectivity.py`; `scripts/diag_report.py`.
