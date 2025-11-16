# Telegram AI Bot

## 1. О проекте
Telegram-бот ProcessOff предоставляет ответы на вопросы по Agile/Scrum. Он отвечает на вопросы по базе знаний (PDF/TXT/MD из `data_pdfs/`), включая вопросы по ретроспективам, SWOT, NVC и т.д. Бот построен на Aiogram + PostgreSQL, RAG реализован через Yandex AI Studio (Search Index + Assistant) и Responses API.

## 2. Запуск проекта
1. Python 3.11+, PostgreSQL (например, в Docker).
2. Проверьте зависимости, затем установите их:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```
3. Скопируйте `.env` из файла `.env.example` (см. секцию ниже).
4. Запустите БД (например, в Docker) и укажите `DATABASE_URL` в `.env`.
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
| `YC_OBS_*` | Ключи к Object Storage, если используется `ingest_yc.py` |
| `MANAGED_RAG_*` | Параметры Responses API (например, для Managed RAG) |

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
- Полный отчёт: `python scripts/diag_report.py` (создаёт `diag_report.md`).

## 6. Релиз (Release 2 – Deployment Automation)
Подробности смотрите в `Yandex_INFRA_SETUP.md`. Ключевые шаги:
1. **Lockbox** для секретов из `.env` > `python export_lockbox_payload.py ...` > сохраните `secret_id`.
2. **Service Accounts** (`telegram-runtime`, `telegram-deploy`, `telegram-build`) с необходимыми ролями (`serverless.containers.admin`, `deploy.editor`, `cloud-build.builder`, `lockbox.payloadViewer` и т.д.).
3. **Container Registry** (`cr.yandex/<registry-id>`); укажите его в `.cloudbuild.yaml` и `deploy-spec.yaml`.
4. **GitHub/Managed GitLab** для исходного кода, который будет забирать Cloud Build.
5. **Cloud Build** триггер на `main`, использующий `.cloudbuild.yaml` для сборки (predeploy, pytest, docker build/push, `yc deploy release run`).
6. **deploy-spec.yaml** с указанием `service-account-id`, `secretId`, переменных окружения и `${BUILD_ID}`.
7. **Мониторинг** с `python scripts/generate_alert_cli.py --spec monitoring_alerts.yaml --var channel-id=... --var container-id=... --var kb-diag-job-id=...` для создания алертов.

## 7. Мониторинг и автоматизация
- Alerts и notification channels описаны в `monitoring_alerts.md`.
- Cron/Serverless Jobs описаны в `Yandex_AUTOMATION.md`.
- Диагностический скрипт `diag_connectivity.py` (запускается как job) и отчёт `diag_report.md`.

## 8. Полезные ссылки
| Файл | Описание |
| --- | --- |
| `Yandex_INFRA_SETUP.md` | Подробный bootstrap YC (Lockbox, SA, Cloud Build, Deploy, Monitoring) |
| `scripts/generate_yc_bootstrap.py` | Генерация `yc`/`docker` команд для получения ID |
| `Yandex_DEPLOY.md`, `Yandex_DEVOPS.md`, `Yandex_SECRETS.md` | Дополнительные инструкции по деплою/CI/CD/секретам |
| `ROADMAP.md`, `BACKLOG.md` | Актуальное состояние проекта (Release 2 – In progress, Release 3 – Planned) |
| `monitoring_alerts.md`, `diag_report.md`, `LAUNCH_CHECKLIST.md` | Мониторинг и контрольные списки |
| `GEMINI_START.md` | Стартовый файл для Gemini-агента: как продолжить работу |

## 9. Ключевые принципы
- Проводить 3 ревью и 5 ретроспектив (см. README/ROADMAP).
- Код: PEP8 + type hints, docstring (Google style), хранение секретов в Lockbox.
- Всегда запускать `predeploy_check.py` и `pytest tests/test_smoke.py`.
- DevOps отвечает за YC/Lockbox/CI/CD, QA – за тесты, Scrum Master/PO – за приоритизацию backlog (Release 2/3).