# Telegram AI Bot (Cloud.ru)

## 1. Overview
ProcessOff — Telegram bot to support Agile/Scrum teams: answers from a knowledge base, produces digests, SWOT/NVC/retro/icebreaker prompts. Stack: Python 3.11, Aiogram, LangGraph, PostgreSQL, local RAG over files on the VM, LLM via Cloud.ru GigaChat. Target infra: Cloud.ru (VM/Container Apps, Managed PostgreSQL, Object Storage/Vault).

## 2. Quickstart (local)
1. Python 3.11+, Docker, [Poetry](https://python-poetry.org/docs/#installation).
2. Install deps:
   ```bash
   poetry install
   ```
3. Copy `.env.example` to `.env` and fill tokens.
4. Run DB (for feedback/logs):
   ```bash
   docker-compose up -d db
   ```
5. Start bot:
   ```bash
   poetry run python main_langgraph.py
   ```

### Environment variables
| Name | Purpose |
| --- | --- |
| `TELEGRAM_BOT_TOKEN` | BotFather token |
| `DATABASE_URL` | PostgreSQL DSN (for compose: `postgresql://user:pass@localhost:5432/ai_bot`) |
| `ADMIN_ID` | Telegram ID of admin |
| `CLOUDRU_TOKEN` / `CLOUDRU_CLIENT_ID` / `CLOUDRU_CLIENT_SECRET` | Cloud.ru GigaChat auth (token or client creds) |

## 3. Knowledge base
1. Place PDF/TXT/MD files into `data_pdfs/knowledge_base/`.
2. Bot loads and caches files on first request; no external search index needed.

## 4. Bot commands
| Command | Description |
| --- | --- |
| `/kb` | Browse knowledge base structure |
| `/ask <question>` | RAG answer |
| `/digest <topic>` | 3–5 bullet digest |
| `/swot`, `/nvc`, `/po_helper`, `/conflict`, `/retro`, `/icebreaker` | Prepared scenarios |
| `/feedback` | Send feedback |

## 5. Checks
- Smoke: `pytest tests/test_smoke.py` (Yandex-specific parts may need disabling)
- Env check: `python check_env.py --env .env --env .env.prod` (legacy YC vars can be ignored)
- Diag: `python diag_connectivity.py` (legacy YC/OBS checks)
- Report: `python scripts/diag_report.py` (writes to `docs/operations/diag_report.md`)

## 6. Deploy / Cloud.ru
- Runtime: Cloud.ru VM/Container Apps + Managed PostgreSQL + OBS/Vault. IaC/workflows: `.github/workflows/terraform-cloudru-v10.yml`, `docs/infra/SBERCLOUD_MIGRATION_PLAN.md`.
- App runs as a single process `python main_langgraph.py`; compose only has `db`. For prod use systemd/Docker with secrets from Vault/OBS (or `.env` for dev).
- RAG/LLM: Cloud.ru GigaChat with local file index on the VM; no Yandex.

## 7. Useful docs
- `docs/README.md` — docs index
- `docs/process/ROADMAP.md`, `docs/process/BACKLOG.md` — releases/backlog (Release 5: Cloud.ru)
- `docs/infra/SBERCLOUD_MIGRATION_PLAN.md`, `docs/infra/SBERCLOUD_CREDENTIALS_GUIDE_V2.md` — Cloud.ru migration/credentials
- `docs/infra/CICD_GUIDE.md`, `docs/infra/DEPLOY_GUIDE.md`, `.github/workflows/terraform-cloudru-v10.yml` — CI/CD and deploy
- `docs/operations/monitoring_alerts.md`, `docs/operations/diag_report.md` — ops guides
- `docs/process/LAUNCH_CHECKLIST.md`, `docs/operations/BOT_IS_RUNNING.md` — checklists
- `docs/onboarding/CODEX_CLI_SETUP.md`, `docs/onboarding/CODex_CLI_NOTES.md` — Codex CLI notes

## 8. Contribution
- Follow PEP8, type hints, docstrings (Google style).
- Before release: `python predeploy_check.py` and `pytest tests/test_smoke.py` (adjust for Cloud.ru if needed).
- DevOps: focus on Cloud.ru (OBS/Vault/Managed PG); QA: smoke/integration; Scrum Master/PO: maintain backlog Release 5.
