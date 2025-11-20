# Telegram AI Bot

## 1. О проекте
Telegram-бот ProcessOff предоставляет ответы на вопросы по Agile/Scrum. Он отвечает на вопросы по базе знаний (PDF/TXT/MD из `data_pdfs/`), включая вопросы по ретроспективам, SWOT, NVC и т.д. Бот построен на Aiogram + PostgreSQL, RAG реализован через Yandex AI Studio (Search Index + Assistant) и Responses API.

## 2. Запуск проекта (локально)
1. Python 3.11+, Docker.
2. Проверьте зависимости, затем установите их:
   ```bash
   pip install -r requirements.txt
   ```
3. Скопируйте `.env` из файла `.env.example`.
4. Запустите БД (например, в Docker) и укажите `DATABASE_URL` в `.env`.
   ```bash
   docker-compose up -d db
   ```
5. Запустите бота:
   ```bash
   python app.py
   ```

### Переменные окружения
| Ключ | Описание |
| --- | --- |
| `TELEGRAM_BOT_TOKEN` | Токен от BotFather |
| `DATABASE_URL` | Строка подключения к PostgreSQL (пример: `postgresql://user:pass@localhost:5432/ai_bot`) |
| `YANDEX_API_KEY` / `YC_API_KEY` | API-ключ Yandex Cloud для SDK/Responses API |
| `YANDEX_FOLDER_ID` / `YC_FOLDER_ID` | ID каталога в Yandex Cloud |
| `YC_SEARCH_INDEX_ID`, `YC_ASSISTANT_ID` | ID Search Index и Assistant из AI Studio |
| `YC_OBS_*` | Ключи к Object Storage |
| `MANAGED_RAG_*` | Параметры Responses API (например, для Managed RAG) |
| `YC_SERVICE_ACCOUNT_KEY_FILE` | Путь к файлу ключа сервисного аккаунта для Lockbox |
| `YC_IAM_TOKEN` | IAM-токен для аутентификации |


## 3. Работа с базой знаний
1. Поместите PDF/TXT/MD в `data_pdfs/knowledge_base`.
2. Загрузите документы в Object Storage + обновите Search Index:
   ```bash
   python ingest_yc.py
   ```
   Скрипт сохранит ID в `.yc_search_index_id`.
3. Создайте ассистента AI Studio с использованием Search Index:
   ```bash
   python create_assistant.py
   ```
   ID ассистента сохранится в `.yc_assistant_id`.
4. Обновите `.env` с полученными ID. Команда `/kb` покажет список документов.

## 4. Команды бота
| Команда | Описание |
| --- | --- |
| `/kb` | Показать документы/темы из базы знаний |
| `/ask <запрос>` | Задать вопрос по RAG |
| `/digest <тема>` | Сделать дайджест (3-5 пунктов) |
| `/swot`, `/nvc`, `/po_helper`, `/conflict`, `/retro`, `/icebreaker` | Специализированные команды (см. в `handlers/llm_commands.py`) |
| `/feedback` | Оставить отзыв (сохраняется в таблицу `feedback`, см. схему) |

## 5. Проверки и диагностика
- Smoke-тесты: `pytest tests/test_smoke.py`.
- Проверка переменных: `python check_env.py --env .env --env .env.prod`.
- Диагностика YC (Postgres/Search Index/Object Storage): `python diag_connectivity.py` (вывод в JSON).
- Полный отчёт: `python scripts/diag_report.py` (создаёт `docs/operations/diag_report.md`).

## 6. Релиз (с использованием GitHub Actions)
1.  **Настройка CI/CD**: Используется GitHub Actions для сборки и развертывания. См. `docs/infra/GITHUB_YC_INTEGRATION.md`.
2.  **Развертывание**: Приложение развертывается в Docker-контейнере на **Yandex Compute Cloud VM**.
3.  **База данных**: **PostgreSQL** развертывается в Docker-контейнере на той же или отдельной VM.
4.  **Секреты**: **Yandex Lockbox** используется для безопасного хранения секретов.

## 7. Мониторинг и автоматизация
- Alerts и notification channels описаны в `docs/operations/monitoring_alerts.md`.
- Cron/Serverless Jobs описаны в `docs/infra/Yandex_AUTOMATION.md`.
- Диагностический скрипт `diag_connectivity.py` (запускается как job) и отчёт `docs/operations/diag_report.md`.
- Terraform план для Cloud.ru запускается через `.github/workflows/infra-cloudru.yml` (секреты `CLOUDRU_TF_BACKEND_HCL`, `CLOUDRU_TFVARS`).

## 8. Полезные ссылки
| Файл | Описание |
| --- | --- |
| `docs/README.md` | Карта документации (процесс, разработка, инфраструктура, операции) |
| `docs/infra/Yandex_INFRA_SETUP.md` | Подробный bootstrap YC (Lockbox, SA, Cloud Build, Deploy, Monitoring) |
| `scripts/generate_yc_bootstrap.py` | Генерация `yc`/`docker` команд для получения ID |
| `scripts/get_cloudru_token.py` | Быстрый запрос IAM-токена Cloud.ru (использует httpx) |
| `docs/infra/Yandex_DEPLOY.md`, `docs/infra/Yandex_DEVOPS.md`, `docs/infra/Yandex_SECRETS.md` | Дополнительные инструкции по деплою/CI/CD/секретам |
| `terraform/README.md` | Настройка Cloud.ru инфраструктуры через Terraform и backend в OBS |
| `docs/process/ROADMAP.md`, `docs/process/BACKLOG.md` | Актуальное состояние проекта (Release 2 – In progress, Release 3 – Planned) |
| `docs/onboarding/CODEX_CLI_SETUP.md`, `docs/onboarding/CODex_CLI_NOTES.md` | Быстрый старт для новых участников и работа через Codex CLI |
| `docs/operations/monitoring_alerts.md`, `docs/operations/diag_report.md`, `docs/process/LAUNCH_CHECKLIST.md` | Мониторинг и контрольные списки |
| `docs/operations/troubleshooting/DB_CONNECTION_ISSUE.md` | Runbook по проблемам подключения к БД |
| `docs/process/GEMINI_START.md` | Стартовый файл для Gemini-агента: как продолжить работу |

## 9. Ключевые принципы
- Проводить 3 ревью и 5 ретроспектив (см. README и `docs/process/ROADMAP.md`).
- Код: PEP8 + type hints, docstring (Google style), хранение секретов в Lockbox.
- Всегда запускать `predeploy_check.py` и `pytest tests/test_smoke.py`.
- DevOps отвечает за YC/Lockbox/CI/CD, QA – за тесты, Scrum Master/PO – за приоритизацию backlog (Release 2/3).
