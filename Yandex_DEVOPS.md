# CI/CD и хранение кода внутри Yandex Cloud

Документ описывает, как организовать полный цикл разработки Telegram AI Bot без GitHub: код хранится в Yandex Cloud DevTools Repositories, сборка/деплой выполняется через сервисы Cloud Build и Cloud Deploy, артефакты размещаются в Container Registry, а секреты выдаёт Lockbox (или Secrets Manager).

## 1. Репозиторий в Yandex Cloud DevTools
1. **Подготовьте сервисный аккаунт** (SA) с ролями:
   - `devtools.repo-admin` – создание репозиториев;
   - `devtools.repo-pusher` – push из CI;
   - `devtools.repo-user` – чтение.
2. **Создайте репозиторий** (через консоль DevTools или CLI):
   ```
   yc devtools repo create \
     --name telegram-ai-bot \
     --description "ProcessOff Telegram bot" \
     --folder-id b1xxx...
   ```
3. **Подключите локально**:
   ```
   git remote add yandex ssh://git@rc1c-<repo-id>.repo.cloud.yandex.net/telegram-ai-bot.git
   git push yandex main
   ```
   SSH ключ можно сгенерировать локально и загрузить в DevTools (раздел *Access keys*).

## 2. Container Registry
1. Создайте реестр:
   ```
   yc container registry create --name telegram-ai-registry
   ```
2. Дайте SA роль `container-registry.images.pusher`.
3. Локальная сборка/публикация:
   ```
   docker build -t cr.yandex/<registry-id>/telegram-ai-bot:latest .
   docker push cr.yandex/<registry-id>/telegram-ai-bot:latest
   ```

## 3. Cloud Build (сборка без GitHub)
Cloud Build умеет забирать код напрямую из DevTools Repo:
1. Создайте файл `.cloudbuild.yaml`:
   ```yaml
   steps:
     - name: docker
       entrypoint: bash
       args:
         - -c
         - |
           docker build -t ${REGISTRY}/telegram-ai-bot:${CI_COMMIT_SHA} .
           docker push ${REGISTRY}/telegram-ai-bot:${CI_COMMIT_SHA}
   substitutions:
     REGISTRY: cr.yandex/<registry-id>
   ```
2. Создайте билд-триггер:
   ```
   yc cloud-build trigger create git \
     --name telegram-ai-trigger \
     --repo-id <devtools-repo-id> \
     --branch main \
     --build-config-file .cloudbuild.yaml \
     --service-account-id <sa-build>
   ```
3. SA для билда должен иметь роли `cloud-build.builder`, `container-registry.images.pusher`, `devtools.repo-reader`.

## 4. Cloud Deploy (развёртывание)
Deploy может брать образ из Container Registry и обновлять Serverless Container.
1. Создайте спецификацию `deploy-spec.yaml`:
   ```yaml
   apiVersion: deploy.yandex.cloud/v1
   kind: ExecutionSpec
   metadata:
     name: telegram-ai-bot
   spec:
     containers:
       - name: app
         image: cr.yandex/<registry-id>/telegram-ai-bot:${CI_COMMIT_SHA}
         concurrency: 1
         memory: 1GiB
         service-account-id: <sa-runtime>
         secrets:
           - name: TELEGRAM_BOT_TOKEN
             valueFrom:
               secretId: <lockbox-secret-id>
               key: TELEGRAM_BOT_TOKEN
         env:
           - name: DATABASE_URL
             value: postgresql://...
           - name: YANDEX_FOLDER_ID
             value: b1xxx...
     destination:
       serverless-container:
         id: <container-id>
   ```
2. Создайте релиз:
   ```
   yc deploy release run \
     --spec deploy-spec.yaml \
     --service-account-id <sa-deploy>
   ```
3. Роли для SA деплоя: `deploy.editor`, `serverless.containers.admin`, `lockbox.payloadViewer`, `mdb.viewer` (для чтения connection строк).

## 5. Секреты: Lockbox/Secrets Manager
1. Создайте секрет:
   ```
   yc lockbox secret create \
     --name telegram-ai-secrets \
     --payload-file secrets.json
   ```
   где `secrets.json`:
   ```json
   {
     "entries": [
       {"key": "TELEGRAM_BOT_TOKEN", "textValue": "xxx"},
       {"key": "YC_API_KEY", "textValue": "AQV..."},
       {"key": "YC_OBS_ACCESS_KEY_ID", "textValue": "YCA..."},
       {"key": "YC_OBS_SECRET_ACCESS_KEY", "textValue": "YC..."}
     ]
   }
   ```
2. В `deploy-spec.yaml` или `yc serverless-container deploy` указывайте `--secrets` с ID Lockbox.
3. Перед деплоем запускайте `python check_env.py --env .env.local --env .env.prod`, чтобы убедиться, что локальные файлы синхронизированы с Lockbox.

## 6. Cron и ingestion
- Для регулярного обновления Search Index создайте Cloud Function или контейнерный job, который вызывает `python ingest_yc.py`. Планировщик (`yc serverless trigger cron create`) будет дергать job раз в N часов. Конкретные команды смотрите в `Yandex_AUTOMATION.md`.
- Для диагностики соединений добавьте job, который выполняет `python diag_connectivity.py` и отправляет отчёты в Logging/Monitoring (подробности в `Yandex_AUTOMATION.md`).

## 7. Pre-deploy проверка в Cloud Build
Чтобы не вносить в облако некорректные конфигурации, добавьте шаг проверки окружения, аналогичный `predeploy_check.py` из GitHub Actions:

```yaml
steps:
  - name: python
    entrypoint: bash
    args:
      - -c
      - |
        pip install -r requirements.txt
        pip install python-dotenv
        python predeploy_check.py --env .env --env .env.prod
        pytest -q tests/test_smoke.py
  - name: docker
    # сборка образа и push

Готовый пример лежит в `.cloudbuild.yaml`. Перед запуском замените `_REGISTRY`, `_DEPLOY_SPEC` и `_DEPLOY_SA` на значения вашего проекта и загрузите файл в репозиторий DevTools.

## 4. Сервисные аккаунты и роли
```bash
# runtime SA для Serverless Container
yc iam service-account create --name telegram-runtime

# deploy SA для Cloud Deploy
yc iam service-account create --name telegram-deploy

# доступы
yc resource-manager folder add-access-binding \
  --id <folder-id> \
  --role serverless.containers.admin \
  --subject serviceAccount:<runtime-sa-id>

yc resource-manager folder add-access-binding \
  --id <folder-id> \
  --role lockbox.payloadViewer \
  --subject serviceAccount:<runtime-sa-id>

yc resource-manager folder add-access-binding \
  --id <folder-id> \
  --role deploy.editor \
  --subject serviceAccount:<deploy-sa-id>

yc resource-manager folder add-access-binding \
  --id <folder-id> \
  --role container-registry.pusher \
  --subject serviceAccount:<deploy-sa-id>
```

Сохраните ID этих SA: `runtime-sa-id` используется в `deploy-spec.yaml`, `deploy-sa-id` — в Cloud Build/Deploy.
```

Таким образом процесс Cloud Build повторяет логику GitHub Actions: сначала проверка env, затем сборка и деплой (через Cloud Deploy).

## 7. Процесс без GitHub
1. Разработчик коммитит локально → `git push yandex feature/my-task`.
2. Product Owner/Scrum Master инициируют merge (через DevTools UI или CLI).
3. Merge в `main` запускает Cloud Build → образ появляется в Container Registry.
4. Cloud Deploy триггерит релиз (автоматически или вручную) и обновляет Serverless Container.
5. check_env.py и Lockbox обеспечивают консистентность секретов; все артефакты и логи находятся внутри Yandex Cloud.

Такой процесс удовлетворяет требованию “без GitHub”: весь цикл (код, секреты, сборка, деплой, мониторинг) находится в сервисах Yandex Cloud.

## 8. Bootstrap-скрипты и автоматизация
- Для быстрого старта используйте Yandex_INFRA_SETUP.md.
- Для генерации команд yc/docker/Lockbox/Deploy используйте "python scripts/generate_yc_bootstrap.py --folder-id [folder] --registry-id [registry] --container-id [container] --secret-id [secret]".
- Роль DevOps-инженера: он отвечает за настройку инфраструктуры, сервисных аккаунтов, Lockbox, docker build/push, Cloud Deploy и мониторинг.