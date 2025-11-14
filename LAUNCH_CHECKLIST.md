# Launch Checklist for Telegram AI Bot (Yandex Cloud)

## Конфигурация окружения
- [ ] `python check_env.py --env .env --env .env.prod` проходит без ошибок.
- [ ] Все секреты перенесены в Lockbox/Secrets Manager (`TELEGRAM_BOT_TOKEN`, `YC_API_KEY`, `YC_OBS_*`, `DATABASE_URL`).
- [ ] `.yc_search_index_id` и `.yc_assistant_id` актуальны и перенесены в `.env.prod`.

## Хранилище знаний
- [ ] Файлы загружены в Object Storage (`processoff-kb/knowledge-base/`).
- [ ] `python ingest_yc.py` выполнен, Search Index создан и записан.
- [ ] `python create_assistant.py` выполнен, ассистент создан.
- [ ] Cron-триггер `kb-ingest-daily` активен (см. `Yandex_AUTOMATION.md`).

## Приложение
- [ ] Docker-образ опубликован в Container Registry (`cr.yandex/...`).
- [ ] Serverless Container обновлён командой `yc serverless container revision deploy ...`.
- [ ] Telegram webhook настроен на публичный endpoint (если используется webhook-режим).
- [ ] Managed PostgreSQL доступен, `DATABASE_URL` обновлён.

## Мониторинг
- [ ] `diag_connectivity.py` job настроен и запускается по cron.
- [ ] Настроены алерты в Monitoring (`serverless.container.errors.count`, `serverless.job.executions.failed_count`).
- [ ] Notification channels (email/Telegram) активны.
- [ ] Дашборд Monitoring создан и отображает основные метрики.

## Документация и процессы
- [ ] README + Yandex_* файлы актуальны и отражают фактический процесс.
- [ ] Правило ретроспектив после каждых 5 ответов соблюдается.
- [ ] Роли команды актуализированы (DevOps/Monitoring объединены при необходимости).

После выполнения всей чек-листа можно запускать прод-версии и проводить финальное UAT/acceptance тестирование.
