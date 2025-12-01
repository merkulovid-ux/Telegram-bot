# Active Context

- Target environment: Cloud.ru; docs and README updated to reflect Cloud.ru focus; bot runs on VM.
- Bot reliability: added error handling in `main_langgraph.py` (try/except around graph calls) and made `analytics.log_event` best-effort to avoid silent failures when DB is down.
- Docs cleanup: `docs/README.md` rewritten; `docs/operations/monitoring_alerts.md` fixed encoding; `README.md` rewritten for Cloud.ru; `.env.example` updated with Cloud.ru creds.
- Memory bank created (core files).
- Constraints: **no Yandex usage**; **no managed RAG from Cloud.ru**. Current code still wired to Yandex RAG/Assistant and needs refactor to a non-Yandex/local pipeline.
- Outstanding: database connectivity still required for full features; feedback insertion still depends on DB; no terraform directory present despite mentions.
- Next immediate step to make bot work on VM: set Cloud.ru creds (`CLOUDRU_TOKEN` or `CLOUDRU_CLIENT_ID/SECRET`), ensure Postgres reachable, place KB files in `data_pdfs/knowledge_base`, restart bot; Yandex dependencies remain in legacy scripts/tests but runtime uses Cloud.ru/local.
