# Documentation Hub

Навигация по документации (целевой стек: Cloud.ru, Telegram-бот ProcessOff, Aiogram + PostgreSQL + локальный RAG).

## 1. Process
- `process/BACKLOG.md`, `process/ROADMAP.md` — релизы и бэклог (Release 5: Cloud.ru).
- `process/TEAM.md`, `process/PROCESS_IMPROVEMENT_PLAN.md` — роли, XP/TDD, DoR/DoD.
- `process/LAUNCH_CHECKLIST.md`, `process/GEMINI_START.md`, `process/CURRENT_TASK_CONTEXT.md` — чек-листы запуска и контекст задач.

## 2. Development
- `development/ARCHITECTURAL_IMPROVEMENTS.md`, `development/refactoring_plan.md`, файлы `REFACTORING_*` — архитектура и рефакторинг.
- `development/CODE_REVIEW.md`, `development/ALL_COMMANDS_REFACTORED.md` — правила код-ревью и история правок.
- `development/PROJECT_DOCS.md`, `development/PROJECT_ANALYSIS.md` — обзор решения и анализ.

## 3. Infrastructure (Cloud.ru)
- `infra/SBERCLOUD_MIGRATION_PLAN.md`, `infra/SBERCLOUD_CREDENTIALS_GUIDE_V2.md` — миграция и учётки Cloud.ru.
- `infra/CICD_GUIDE.md`, `infra/DEPLOY_GUIDE.md` — CI/CD и деплой.
- `infra/INFRASTRUCTURE_IMPROVEMENT_PROPOSAL.md`, `infra/role_storage_uploader.md` — предложения и роли.
- Cloud.ru KB: `docs/cloudru_kb/*` (terraform provider, managed postgres, container apps, checklist).
- Исторические YC-материалы (`infra/GITHUB_YC_INTEGRATION.md`, `infra/SERVICE_ACCOUNT_INSTRUCTIONS.md`) — для справки.

## 4. Operations
- `operations/monitoring_alerts.md` — алерты/дашборды.
- `operations/diag_report.md`, `operations/TEST_RESULTS.md` — примеры диагностики и тестов.
- `operations/RESTORE_DB_INSTRUCTIONS.md`, `operations/BOT_IS_RUNNING.md` — runbook’и по БД и статусу бота.
- `operations/troubleshooting/DB_CONNECTION_ISSUE.md` — подключение к PostgreSQL.

## 5. Onboarding & CLI
- `onboarding/CODEX_CLI_SETUP.md`, `onboarding/CODex_CLI_NOTES.md` — настройка Codex CLI.

## 6. Archive & exports
- `archive/ai_studio.html`, `archive/pdf_searchindex.html`, `archive/rag.html` — сохранённые UI/экспорты.
- `archive/README.md.utf8`, `archive/README.tmp2`, `archive/release2_package.json` — исторические артефакты.

## 7. Как читать
1. Про процессы и бэклог — `process/`.
2. Про код и архитектуру — `development/` + корневой `README.md`.
3. Про инфраструктуру Cloud.ru — `infra/` и `cloudru_kb/`.
4. Про эксплуатацию — `operations/`.
