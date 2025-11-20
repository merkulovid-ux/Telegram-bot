# Monitoring & Alerts Playbook

## Serverless Container
- **Metric**: `serverless.container.errors.count`
- **Alert specification (yaml)**:
  ```yaml
  name: telegram-container-errors
  metric: serverless.container.errors.count
  comparison: GT
  threshold: 0
  aggregation: mean
  period: 300
  labels:
    container_id: <container-id>
  notification_channels:
    - <channel-id>
  ```
- **CLI**:
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

## Serverless Job (ingest/diag)
- **Metric**: `serverless.job.executions.failed_count`
- **CLI**:
  ```bash
  yc monitoring alert create \
    --name kb-diag-failed \
    --metric serverless.job.executions.failed_count \
    --comparison GT \
    --threshold 0 \
    --aggregation mean \
    --period "15m" \
    --notification-channel-id <channel-id> \
    --labels job_id=<kb-diag-job-id>
  ```

## Notification Channels
- Email:
  ```bash
  yc monitoring notification-channel create email \
    --name alerts-email \
    --email ops@processoff.com
  ```
- Telegram via webhook (���? �?�?�'�?�?�?�?�? ����?���>�? �? Monitoring).

## Automation via CLI script
- Сгенерировать команды из `monitoring_alerts.yaml`:
  ```bash
  python scripts/generate_alert_cli.py --spec monitoring_alerts.yaml
  ```
- Только каналы или только алерты:
  ```bash
  python scripts/generate_alert_cli.py --channels-only
  python scripts/generate_alert_cli.py --alerts-only
  ```
- Подстановка ID вместо плейсхолдеров `<...>`:
  ```bash
  python scripts/generate_alert_cli.py --var channel-id=b1abcde1 \
    --var container-id=bbcefg123 --var kb-diag-job-id=ajet111
  ```
  `--var KEY=VALUE` можно повторять — он заменяет `<KEY>` во всех командах.

## Dashboards
���?���?�����'�� `dashboard.json` �? �?�?���"�����?��:
- `serverless.container.requests.count` (by status)
- `serverless.container.errors.count`
- `serverless.job.executions.count`
- `serverless.job.executions.failed_count`

```bash
yc monitoring dashboard create --file dashboard.json
```

## ����?�>���?��?�'
- �?�?�?�?��?��� �?���?�+�?�?�?�� ����?�?��?�?�?.
- �������Ő�? �?�� ���>��?�'�< �%�30 �?��?�?�'.
- �?�?�?�>�� ��?�Ő�?��?�'�� �?" ��������?�? �? ��?�?�?���> (�?�?. Yandex_MONITORING.md).
