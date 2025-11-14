# Автоматизация ingestion и диагностики в Yandex Cloud

Чтобы минимизировать ручные операции, вынесем периодический запуск `ingest_yc.py` и `diag_connectivity.py` в контейнерные job’ы (Serverless Jobs) с cron-триггерами. Они используют те же секреты (Lockbox) и переменные, что и прод-контейнер.

## 1. Подготовка образа
Используем тот же Dockerfile, но добавим entrypoint-параметры:
```bash
docker build -t cr.yandex/<registry-id>/telegram-ai-bot:latest .
docker push cr.yandex/<registry-id>/telegram-ai-bot:latest
```

## 2. Job для ingestion (ingest_yc.py)
Создаём job:
```bash
yc serverless job create \
  --name kb-ingest-job \
  --description "Обновление Search Index" \
  --image cr.yandex/<registry-id>/telegram-ai-bot:latest \
  --service-account-id <sa-job> \
  --environment DATABASE_URL=<...> \
  --secrets TELEGRAM_BOT_TOKEN=<lockbox-secret-id>:TELEGRAM_BOT_TOKEN,YC_API_KEY=<lockbox-secret-id>:YC_API_KEY \
  --command "python" \
  --args "ingest_yc.py"
```
*Секреты перечисляем в формате `--secrets NAME=<secret-id>:<key>`; можно вынести все переменные в Lockbox и передавать через `--environment-from-secrets`.*

Cron-триггер (раз в сутки):
```bash
yc serverless trigger cron create \
  --name kb-ingest-daily \
  --cron-expression "0 3 * * *" \
  --job-id <kb-ingest-job-id> \
  --invoke-once
```
`--invoke-once` запускает job каждый раз согласно расписанию. При необходимости поставьте `--retry-attempts` и `--retry-interval`.

## 3. Job для диагностики (diag_connectivity.py)
```bash
yc serverless job create \
  --name kb-diag-job \
  --description "Диагностика Object Storage и Search Index" \
  --image cr.yandex/<registry-id>/telegram-ai-bot:latest \
  --service-account-id <sa-job> \
  --environment DATABASE_URL=<...> \
  --secrets YC_OBS_ACCESS_KEY_ID=<lockbox>:YC_OBS_ACCESS_KEY_ID,YC_OBS_SECRET_ACCESS_KEY=<lockbox>:YC_OBS_SECRET_ACCESS_KEY \
  --command "python" \
  --args "diag_connectivity.py"
```
Cron-триггер (каждые 6 часов):
```bash
yc serverless trigger cron create \
  --name kb-diag-6h \
  --cron-expression "0 */6 * * *" \
  --job-id <kb-diag-job-id> \
  --retry-attempts 3 \
  --retry-interval 60s
`n`n`diag_connectivity.py` ������� JSON-������ �� ������� ���������� (postgresql, search_index, object_storage) � ��������� ������ � ����� 1 ��� �������. ��� �������� ���������� ������� � Cloud Logging (��. `Yandex_MONITORING.md`).
```

## 4. Логи и мониторинг
- Job’ы автоматически пишут stdout/stderr в Cloud Logging (`yc logging read`). Настройте алерт в Monitoring на ошибки (`severity>=ERROR`).
- Можно отправлять отчёт в Telegram/почту через отдельную функцию, но минимум — проверять Cloud Logging и статусы job’ов (`yc serverless job execution list`).

## 5. Обновление образа
После релиза приложения (см. `Yandex_DEVOPS.md`) job’ы можно обновить:
```bash
yc serverless job update <job-id> --image cr.yandex/<registry-id>/telegram-ai-bot:<new-tag>
```

## 6. Проверка секретов
Перед расписанием запусков выполните `python check_env.py --env .env --env .env.prod`, убедитесь, что все переменные совпадают с Lockbox/Secrets Manager.

Такой подход полностью автономен: ingestion и диагностика идут по расписанию внутри Yandex Cloud, без ручных запусков.
