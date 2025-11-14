# Telegram AI Bot

## 1. Что это такое
Телеграм-бот ProcessOff помогает командам по Agile/Scrum. Он отвечает на вопросы из базы знаний (PDF/TXT/MD в `data_pdfs/`), умеет делать дайджесты, SWOT, NVC и т.д. Бэкенд построен на Aiogram + PostgreSQL, RAG работает через Yandex AI Studio (Search Index + Assistant) и Responses API.

## 2. Быстрый старт локально
1. Python 3.11+, PostgreSQL (можно из Docker).
2. Склонируй репозиторий, создай виртуальное окружение:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```
3. Заполни `.env` на основе `.env.example` (см. таблицу ниже).
4. Подними БД (локально или в Docker) и задай `DATABASE_URL` в `.env`.
5. Запусти бота:
   ```bash
   python app.py
   ```

### Обязательные переменные
| Имя | Назначение |
| --- | --- |
| `TELEGRAM_BOT_TOKEN` | токен от BotFather |
| `DATABASE_URL` | строка подключения к PostgreSQL (пример: `postgresql://user:pass@localhost:5432/ai_bot`) |
| `YANDEX_API_KEY` / `YC_API_KEY` | API?ключ Yandex Cloud для SDK/Responses API |
| `YANDEX_FOLDER_ID` / `YC_FOLDER_ID` | ID каталога в Yandex Cloud |
| `YC_SEARCH_INDEX_ID`, `YC_ASSISTANT_ID` | ID Search Index и Assistant из AI Studio |
| `YC_OBS_*` | доступы к Object Storage, если используешь `ingest_yc.py` |
| `MANAGED_RAG_*` | параметры Responses API (опционально, для Managed RAG) |

## 3. Импорт базы знаний
1. Сложи PDF/TXT/MD в `data_pdfs/категория`.
2. Запусти загрузку в Object Storage + создание Search Index:
   ```bash
   python ingest_yc.py
   ```
   Скрипт сохранит ID в `.yc_search_index_id`.
3. Создай ассистента AI Studio и привяжи Search Index:
   ```bash
   python create_assistant.py
   ```
   ID сохранится в `.yc_assistant_id`.
4. Обнови `.env` и перезапусти бота. Команда `/kb` подтянет свежую структуру.

## 4. Команды бота
| Команда | Назначение |
| --- | --- |
| `/kb` | просмотр категорий/тем из базы знаний |
| `/ask <вопрос>` | ответ из RAG |
| `/digest <тема>` | короткий дайджест (3–5 тезисов) |
| `/swot`, `/nvc`, `/po_helper`, `/conflict`, `/retro`, `/icebreaker` | специализированные режимы (описаны в `handlers/llm_commands.py`) |
| `/feedback` | отправить отзыв (пишется в таблицу `feedback`, форвард админу) |

## 5. Тесты и диагностика
- Смоук?тест: `pytest tests/test_smoke.py`.
- Проверка окружения: `python check_env.py --env .env --env .env.prod`.
- Диагностика YC (Postgres/Search Index/Object Storage): `python diag_connectivity.py` (лог в JSON).
- Для отчёта: `python scripts/diag_report.py` (обновит `diag_report.md`).

## 6. Деплой (Release 2 — Deployment Automation)
Полный чеклист лежит в `Yandex_INFRA_SETUP.md`. Суть:
1. **Lockbox** — выгрузить `.env` > `python export_lockbox_payload.py ...` > создать секрет и получить `secret_id`.
2. **Service Accounts** — `telegram-runtime`, `telegram-deploy`, `telegram-build` с минимальными ролями (`serverless.containers.admin`, `deploy.editor`, `cloud-build.builder`, `lockbox.payloadViewer` и т.д.).
3. **Container Registry** — `cr.yandex/<registry-id>`; используем его в `.cloudbuild.yaml` и `deploy-spec.yaml`.
4. **GitHub/Managed GitLab** — код должен жить в репо, которое видит Cloud Build.
5. **Cloud Build** — триггер по `main`, файл `.cloudbuild.yaml` уже готов (predeploy, pytest, docker build/push, `yc deploy release run`).
6. **deploy-spec.yaml** — пропиши `service-account-id`, `secretId`, реальные ENV и образ `${BUILD_ID}`.
7. **Мониторинг** — `python scripts/generate_alert_cli.py --spec monitoring_alerts.yaml --var channel-id=... --var container-id=... --var kb-diag-job-id=...` и создай alert'ы.

## 7. Мониторинг и поддержка
- Alerts и notification channels — `monitoring_alerts.md`.
- Cron/Serverless Jobs — `Yandex_AUTOMATION.md`.
- Регулярно запускай `diag_connectivity.py` (можно как job) и публикуй `diag_report.md`.

## 8. Где что лежит
| Файл | Что внутри |
| --- | --- |
| `Yandex_INFRA_SETUP.md` | детальный bootstrap YC (Lockbox, SA, Cloud Build, Deploy, Monitoring) |
| `scripts/generate_yc_bootstrap.py` | печатает все нужные `yc`/`docker` команды под твои ID |
| `Yandex_DEPLOY.md`, `Yandex_DEVOPS.md`, `Yandex_SECRETS.md` | расширенные инструкции по деплою/CI/CD/секретам |
| `ROADMAP.md`, `BACKLOG.md` | актуальный продуктовый план (Release 2 — In progress, Release 3 — Planned) |
| `monitoring_alerts.md`, `diag_report.md`, `LAUNCH_CHECKLIST.md` | наблюдаемость и контроль релизов |
| `GEMINI_START.md` | стартовый файл для ИИ-агента: что проверить перед задачей |

## 9. Правила команды
- Каждые 3 ответа — короткий refinement, каждые 5 — ретро (см. README/ROADMAP).
- Код: PEP8 + type hints, docstring (Google style), секреты только в Lockbox.
- Перед деплоем обязательно `predeploy_check.py` и `pytest tests/test_smoke.py`.
- DevOps отвечает за YC/Lockbox/CI/CD, QA — за тесты, Scrum Master/PO — за синхронизацию backlog (Release 2/3).
