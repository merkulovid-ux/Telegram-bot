# Логирование и мониторинг в Yandex Cloud

Цель документа — описать, как наблюдать за Telegram AI Bot после миграции в инфраструктуру Yandex Cloud: сбор логов, метрик и настройка алертов на сбои ingestion/диагностики.

## 1. Логи Serverless Container
Serverless Containers пишут stdout/stderr в Cloud Logging автоматически.

### Просмотр логов
```bash
yc logging read \
  --resource-id <container-id> \
  --since 1h \
  --format=json > logs.json
```
Или через консоль (Logging → Log groups → container). Для фильтрации ошибок используйте запрос:
```
severity >= ERROR
```

### Экспорт логов
Чтобы хранить логи дольше, настройте экспорт в Object Storage:
```bash
yc logging sink create \
  --name telegram-bot-sink \
  --description "Export serverless logs" \
  --log-group-id <log-group-id> \
  --storage-bucket <bucket-name> \
  --service-account-id <sa-logging>
```
`sa-logging` должен иметь роль `logging.reader` и доступ к бакету.

## 2. Логи Serverless Jobs (ingest/diag)
Job’ы (`kb-ingest-job`, `kb-diag-job`) также пишут логи в Cloud Logging. Используйте `yc logging read --resource-id <job-id>` или фильтр по `resource_type="serverless.job"`.

Для отслеживания провалов задайте фильтр:
```
resource_type="serverless.job"
jsonPayload.event_status!="STATUS_COMPLETED"
```

## 3. Метрики и Monitoring
Serverless Container публикует базовые метрики (invocations, duration, errors). Job’ы — количество запусков/ошибок. Проверяйте их в Monitoring → Metrics Explorer.

### Создание дашборда
```bash
yc monitoring dashboard create --file dashboard.json
```
Пример JSON включает графики:
- `serverless.container.requests.count` (by status)
- `serverless.container.errors.count`
- `serverless.job.executions.count`
- `serverless.job.executions.failed_count`

## 4. Алерты
Создайте алерты на ошибки контейнера и job’ов.

### Ошибки контейнера
```bash
yc monitoring alert create \
  --name telegram-container-errors \
  --metric serverless.container.errors.count \
  --comparison GT \
  --threshold 0 \
  --aggregation mean \
  --period "5m" \
  --notification-channel-id <channel-id> \
  --labels container_id=<container-id>
```
Аналогично настройте алерт на `serverless.job.executions.failed_count` для job’ов `kb-ingest` и `kb-diag`.

### Каналы уведомлений
Поддерживаются email, Telegram, Webhook. Пример создания email канала:
```bash
yc monitoring notification-channel create email \
  --name alerts-email \
  --email my-team@processoff.com
```

## 5. Диагностика и отчётность
- В `diag_connectivity.py` можно добавить вывод ключевых параметров (ping OBS, статус индекса), чтобы они попадали в логи.
- Скрипт `diag_connectivity.py` уже печатает JSON-записи для каждого компонента и итоговый статус. В Cloud Logging фильтруйте по `jsonPayload.component="summary"` и `status="FAILED"`, чтобы строить алерты.
- Для ручной проверки выполните:
  ```bash
  yc serverless job execution list --job-name kb-diag-job --limit 5
  yc serverless job execution get --id <execution-id>
  ```
- Если нужна историческая статистика, экспортируйте логи/job executions в ClickHouse (Data Transfer) и анализируйте там.

## 6. Регламент
1. Ежедневно проверять дашборд Monitoring.
2. На каждый алерт реагировать в течение 30 минут.
3. После инцидента фиксировать причину и обновлять инструкции.

Интеграция логов/мониторинга с остальными процессами описана в `Yandex_AUTOMATION.md` и `Yandex_DEVOPS.md`. Перед релизами проверяйте, что алерты активны, а notification канал доступен.
