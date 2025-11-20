# Documentation Hub

Эта директория собирает документацию по четырём основным направлениям: процесс, разработка, инфраструктура и эксплуатация. Таблица ниже помогает быстрее находить нужные артефакты.

## 1. Process
- `process/BACKLOG.md`, `process/ROADMAP.md` — актуальные приоритеты, цели релизов.
- `process/TEAM.md`, `process/PROCESS_IMPROVEMENT_PLAN.md` — роли, XP/TDD-практики, DoR/DoD.
- `process/LAUNCH_CHECKLIST.md`, `process/GEMINI_START.md`, `process/CURRENT_TASK_CONTEXT.md` — чеклисты запуска, инструкции по включению в работу.

## 2. Development
- `development/ARCHITECTURAL_IMPROVEMENTS.md`, `development/refactoring_plan.md` и файлы `REFACTORING_*` — эволюция архитектуры и история рефакторингов.
- `development/CODE_REVIEW.md`, `development/ALL_COMMANDS_REFACTORED.md` — требования к качеству кода и реализации команд.
- `development/PROJECT_DOCS.md`, `development/PROJECT_ANALYSIS.md` — обзор продукта и технических решений.

## 3. Infrastructure
- `infra/Yandex_*`, `infra/GITHUB_YC_INTEGRATION.md`, `infra/SERVICE_ACCOUNT_INSTRUCTIONS.md` — текущее состояние YC-стека.
- `infra/SBERCLOUD_*`, `infra/INFRASTRUCTURE_IMPROVEMENT_PROPOSAL.md` — материалы для миграции в Cloud.ru/SberCloud и развития IaC.
- `infra/CICD_GUIDE.md`, `infra/DEPLOY_GUIDE.md` — пайплайны, релизный процесс, доступы.
- `../terraform/README.md` — как поднимать инфраструктуру Cloud.ru через Terraform (модули `network`, `managed_pg` готовы).

## 4. Operations
- `operations/monitoring_alerts.*` — алерты и конфигурации мониторинга.
- `operations/diag_report.md`, `operations/TEST_RESULTS.md` — диагностика окружений и регрессионные сводки.
- `operations/RESTORE_DB_INSTRUCTIONS.md`, `operations/BOT_IS_RUNNING.md` — runbook'и для восстановления сервисов и проверки состояния бота.

## 5. Onboarding & CLI
- `onboarding/CODEX_CLI_SETUP.md`, `onboarding/CODex_CLI_NOTES.md` — как готовить окружение и контекст перед передачей управления Codex CLI.
- Используйте эти инструкции для синхронизации новых участников и документирования активных задач/ресурсов.

## 6. Troubleshooting
- `operations/troubleshooting/DB_CONNECTION_ISSUE.md` — частые проблемы с подключением к PostgreSQL и шаги проверки.
- При обнаружении новых инцидентов добавляйте отдельные markdown-файлы с чётким описанием симптомов и решений.

## 7. Archive & exports
- `archive/ai_studio.html`, `archive/pdf_searchindex.html`, `archive/rag.html` — экспортированные UI-страницы/отчёты.
- `archive/README.md.utf8`, `archive/README.tmp2`, `archive/release2_package.json` — исторические версии документации и пакетов релиза.
- Храните здесь устаревшие материалы, чтобы корень репозитория оставался чистым.

## 8. Обновление структуры
1. Новые документы раскладывайте по этим подпапкам, именуйте файлы по назначению (process/..., infra/...).
2. При переносе файлов обновляйте ссылки в `README.md`, `docs/README.md` и профилирующих инструкциях.
3. Для крупных изменений фиксируйте задачу в `docs/process/BACKLOG.md` и отмечайте исполнителей согласно ролевой модели (Scrum Master, DevOps, QA и т.д.).

Такой порядок упрощает поиск материалов при миграции в Cloud.ru, ревью кода и подготовке релизов. При необходимости можно расширять структуру дополнительными подпапками (например, `infra/terraform/`, `operations/postmortems/`), сохраняя единые принципы классификации.

