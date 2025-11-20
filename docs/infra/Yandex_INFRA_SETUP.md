# Yandex Cloud Infrastructure Setup

## 1. Secrets and Lockbox
1. Экспортируем текущие `.env` данные в JSON:
   ```bash
   python export_lockbox_payload.py --env .env --env .env.prod --output secrets.json
   ```
2. Создаём секрет и первую версию:
   ```bash
   yc lockbox secret create \
     --name telegram-ai-bot \
     --payload-file secrets.json \
     --description "Secrets for Telegram AI Bot"

   yc lockbox secret add-version \
     --id <secret-id> \
     --payload-file secrets.json
   ```
3. В `deploy-spec.yaml` и `yc serverless container revision deploy` используем пары `<secret-id>:<key>`.

## 2. Service Accounts and IAM roles
| Назначение | Команда создания | Обязательные роли |
| --- | --- | --- |
| Runtime (Serverless Container) | `yc iam service-account create --name telegram-runtime` | `serverless.containers.admin`, `lockbox.payloadViewer`, `vpc.user` (если нужен доступ к БД) |
| Deploy (Cloud Deploy/manual) | `yc iam service-account create --name telegram-deploy` | `deploy.editor`, `container-registry.pusher`, `lockbox.payloadViewer` |
| Build (Cloud Build) | `yc iam service-account create --name telegram-build` | `cloud-build.builder`, `container-registry.pusher`, `devtools.repo-reader`, `lockbox.payloadViewer` |

Привязка ролей к папке `<folder-id>`:
```bash
yc resource-manager folder add-access-binding --id <folder-id> \
  --role serverless.containers.admin --subject serviceAccount:<runtime-sa-id>
yc resource-manager folder add-access-binding --id <folder-id> \
  --role lockbox.payloadViewer --subject serviceAccount:<runtime-sa-id>
yc resource-manager folder add-access-binding --id <folder-id> \
  --role deploy.editor --subject serviceAccount:<deploy-sa-id>
yc resource-manager folder add-access-binding --id <folder-id> \
  --role container-registry.pusher --subject serviceAccount:<deploy-sa-id>
yc resource-manager folder add-access-binding --id <folder-id> \
  --role cloud-build.builder --subject serviceAccount:<build-sa-id>
yc resource-manager folder add-access-binding --id <folder-id> \
  --role devtools.repo-reader --subject serviceAccount:<build-sa-id>
```

## 3. Container Registry and Docker image
```bash
yc container registry create --name telegram-ai-registry
docker build -t cr.yandex/<registry-id>/telegram-ai-bot:${TAG} .
docker push cr.yandex/<registry-id>/telegram-ai-bot:${TAG}
```
`TAG` = `BUILD_ID` из Cloud Build или ручное значение.

## 4. DevTools Repo and Cloud Build
1. Создаём репозиторий:
   ```bash
   yc devtools repo create --name telegram-ai-bot --description "ProcessOff Telegram bot"
   git remote add yandex ssh://git@rc1c-<repo-id>.repo.cloud.yandex.net/telegram-ai-bot.git
   git push yandex main
   ```
2. Настраиваем Cloud Build триггер:
   ```bash
   yc cloud-build trigger create git \
     --name telegram-ai-trigger \
     --repo-id <devtools-repo-id> \
     --branch main \
     --build-config-file .cloudbuild.yaml \
     --service-account-id <build-sa-id>
   ```
3. `.cloudbuild.yaml` включает:
   - шаг Python: `pip install`, `python predeploy_check.py --env .env --env .env.prod`, `pytest tests/test_smoke.py`;
   - шаг Docker: `docker build/push` в `cr.yandex/...`;
   - шаг Deploy: `yc deploy release run --spec deploy-spec.yaml --service-account-id <deploy-sa-id>`.

## 5. Serverless Container и Deploy
1. Проверяем `deploy-spec.yaml`: образ `cr.yandex/<registry-id>/telegram-ai-bot:<tag>`, `service-account-id: <runtime-sa-id>`, `secrets` с Lockbox ID.
2. Ручной релиз (если нужно):
   ```bash
   yc deploy release run \
     --spec deploy-spec.yaml \
     --service-account-id <deploy-sa-id> \
     --labels build_id=${TAG} \
     --description "deploy ${TAG}"
   ```
3. Альтернатива без Cloud Deploy:
   ```bash
   yc serverless container revision deploy \
     --container-id <container-id> \
     --image cr.yandex/<registry-id>/telegram-ai-bot:${TAG} \
     --service-account-id <runtime-sa-id> \
     --memory 1g --cores 1 \
     --env DATABASE_URL=postgresql://... \
     --secrets TELEGRAM_BOT_TOKEN=<secret-id>:TELEGRAM_BOT_TOKEN
   ```

## 6. Managed PostgreSQL и Object Storage
- Создаём перенаправление VPC/SG и Managed PostgreSQL instance (`yc managed-postgresql cluster create ...`).
- Обновляем `DATABASE_URL` в Lockbox / `.env.prod`.
- Загружаем документы в Object Storage `processoff-kb/knowledge-base/` и запускаем `python ingest_yc.py` → `python create_assistant.py` (ID сохраняем в `.yc_*`).

## 7. Automation and Monitoring
1. Serverless Job для `diag_connectivity.py` и ingestion cron (`Yandex_AUTOMATION.md`).
2. Alerts и notification channels:
   ```bash
   python scripts/generate_alert_cli.py --spec monitoring_alerts.yaml \
     --var channel-id=<channel-id> \
     --var container-id=<container-id> \
     --var kb-diag-job-id=<job-id>
   ```
   Выполнить команды `yc monitoring notification-channel create ...` и `yc monitoring alert create ...`.
3. Проверяем `diag_report.md`, `monitoring_alerts.md` и дашборды.

## 8. Ответственность ролей
- DevOps Engineer: шаги 1–7, поддержка Lockbox/CI/CD.
- QA Lead: контроль `predeploy_check.py`, `pytest`, smoke-тестов.
- Scrum Master / Product Owner: координация по BL-02 (Deployment Automation) и BL-03 (Monitoring), запуск refinement/retro по регламенту README (refinement каждые 3 ответа, ретро каждые 5).

