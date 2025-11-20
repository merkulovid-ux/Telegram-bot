# Launch Checklist for Telegram AI Bot (Yandex Cloud)

## Проверка конфигурации
- [ ] `python check_env.py --env .env --env .env.prod` проходит успешно.
- [ ] Все секреты загружены в Lockbox/Secrets Manager (`TELEGRAM_BOT_TOKEN`, `YC_API_KEY`, `YC_OBS_*`, `DATABASE_URL`).
- [ ] `.yc_search_index_id` и `.yc_assistant_id` присутствуют и актуальны в `.env`.

## Подготовка данных
- [ ] База знаний загружена в Object Storage (`processoff-kb/knowledge-base/`).
- [ ] `python ingest_yc.py` выполнен, Search Index создан и наполнен.
- [ ] `python create_assistant.py` выполнен, ассистент создан.
- [ ] Cron-триггер `kb-ingest-daily` активен (см. `Yandex_AUTOMATION.md`).

## Развертывание
- [ ] Docker-образ опубликован в Container Registry (`cr.yandex/...`).
- [ ] Serverless Container успешно развернут `yc serverless container revision deploy ...`.
- [ ] Telegram webhook настроен на публичный endpoint (если используется webhook-модель).
- [ ] Managed PostgreSQL настроен, `DATABASE_URL` актуален.

## Мониторинг
- [ ] `diag_connectivity.py` job запущен и настроен по cron.
- [ ] Настроены алерты в Monitoring (`serverless.container.errors.count`, `serverless.job.executions.failed_count`).
- [ ] Notification channels (email/Telegram) настроены.
- [ ] Дашборды Monitoring отображают корректные метрики.

## Документация и процессы
- [ ] README + Yandex_* файлы актуальны и переведены в UTF-8.
- [ ] Проведены все необходимые ревью и ретроспективы (минимум 5).
- [ ] Все критические процессы автоматизированы (DevOps/Monitoring настроены для автоматического реагирования).

После прохождения всех пунктов бот готов к запуску и дальнейшей работе.