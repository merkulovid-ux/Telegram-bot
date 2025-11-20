# Управление секретами в Yandex Cloud

Этот документ помогает синхронизировать переменные окружения (.env, check_env.py, predeploy_check.py) с Lockbox/Secrets Manager и использовать их в Serverless Containers, Jobs и Cloud Build.

## 1. Создание секрета
```bash
yc lockbox secret create \
  --name telegram-ai-bot \
  --payload-file secrets.json \
  --description "Secrets for Telegram AI Bot"
```
`secrets.json`:
```json
{
  "entries": [
    {"key": "TELEGRAM_BOT_TOKEN", "textValue": "xxx"},
    {"key": "YC_API_KEY", "textValue": "AQV..."},
    {"key": "YC_OBS_ACCESS_KEY_ID", "textValue": "YCA..."},
    {"key": "YC_OBS_SECRET_ACCESS_KEY", "textValue": "YC..."},
    {"key": "DATABASE_URL", "textValue": "postgresql://..."}
  ]
}
```

## 2. Добавление/обновление версии
```bash
yc lockbox secret add-version \
  --id <secret-id> \
  --payload-file secrets.json
```
Каждая версия может содержать только изменённые ключи. Предыдущие версии доступны для отката.

## 3. Получение значений (для проверки)
```bash
yc lockbox secret get \
  --id <secret-id> \
  --output json
```
Используйте только для диагностики. В CI/Serverless значения подтягиваются автоматически через `--secrets`.

## 4. Синхронизация с `.env` и `check_env.py`
1. После обновления Lockbox скачайте значения и обновите `.env`, `.env.prod`, `.env.local`.
2. Запустите:
   ```bash
   python check_env.py --env .env --env .env.prod
   python predeploy_check.py --env .env --env .env.prod
   ```
   Это гарантирует, что локальные файлы совпадают с секретами, и CI не упадёт.

## 5. Использование в Serverless Container
```bash
yc serverless container revision deploy \
  --container-name telegram-ai-bot \
  --image cr.yandex/<registry-id>/telegram-ai-bot:<tag> \
  --secrets TELEGRAM_BOT_TOKEN=<secret-id>:TELEGRAM_BOT_TOKEN,YC_API_KEY=<secret-id>:YC_API_KEY \
  --env DATABASE_URL=postgresql://... \
  ...
```
Параметр `secret-id:key` указывает, какой ключ из Lockbox передать как переменную окружения.

## 6. Использование в Serverless Job / Cron
Для ingestion/diag job'ов (см. `Yandex_AUTOMATION.md`) используйте те же `--secrets`. Это убирает необходимость хранить ключи в Docker-образе.

## 7. Cloud Build / Deploy
- Cloud Build: подключите сервисный аккаунт с ролью `lockbox.payloadViewer` и используйте `envFromSecret` (или скачивайте значения для `predeploy_check.py` при необходимости).
- Cloud Deploy: в `deploy-spec.yaml` указывайте `secrets` → `lockboxSecretId`.

## 8. Ротация и аудит
- Каждые 90 дней создавайте новую версию секрета и обновляйте переменные (`check_env.py` поможет выявить пропуски).
- Включите Audit Trails для Lockbox, чтобы отслеживать доступы.

Документ связан с `Yandex_DEVOPS.md` (CI/CD), `Yandex_AUTOMATION.md` (job'ы) и `README.md` (основной процесс). Перед релизом убедитесь, что чек-лист из `LAUNCH_CHECKLIST.md` отмечен, а секреты актуальны.
После обновления Lockbox, синхронизируйте secrets.json с файлами .env, запустив python export_lockbox_payload.py --env .env --env .env.prod --output secrets.json. Это гарантирует, что локальные файлы совпадают с секретами, и CI не упадёт.