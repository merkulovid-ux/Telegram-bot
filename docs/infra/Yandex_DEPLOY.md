# Деплой в Yandex Cloud

Это дополнение к README и DEPLOY_GUIDE: здесь пошагово описаны действия по запуску Telegram-бота на инфраструктуре Yandex, созданию секретов и подготовке Managed RAG.

## 1. Подготовка секретов и переменных
1. Получите API-ключ сервисного аккаунта с ролями `ai.assistants.editor` и `ai.languageModels.user`. Этот ключ будет использоваться в SDK и в Secrets Manager.
2. Создайте секреты через `yc secrets create` — они останутся в каталоге и не попадут в репозиторий:

```
yc secrets create --name TELEGRAM_BOT_TOKEN --data TELEGRAM_BOT_TOKEN=<bot token>
yc secrets create --name YC_API_KEY --data YC_API_KEY=<apikey>
yc secrets create --name YC_FOLDER_ID --data YC_FOLDER_ID=<folder id>
yc secrets create --name YC_OBS_ACCESS_KEY_ID --data YC_OBS_ACCESS_KEY_ID=<access key>
yc secrets create --name YC_OBS_SECRET_ACCESS_KEY --data YC_OBS_SECRET_ACCESS_KEY=<secret>
```

Секреты `TELEGRAM_BOT_TOKEN`, `YC_API_KEY`, `YC_FOLDER_ID`, `YC_OBS_*` используются как переменные окружения внутри контейнера. Не передавайте их в логи.

### Переменные окружения (минимум)
- `TELEGRAM_BOT_TOKEN` — токен бота из BotFather.
- `DATABASE_URL` — строка подключения к PostgreSQL (локально или Managed PostgreSQL).
- `YC_API_KEY` / `YANDEX_API_KEY` — ключи для вызова моделей и ассистента.
- `YC_FOLDER_ID` / `YANDEX_FOLDER_ID` — идентификатор каталога, где создаются ассистенты и индексы.
- `YC_OBS_*` — доступ к Object Storage (идентификатор ключа, секрет, endpoint, регион, бакет, префикс).
- `YC_SEARCH_INDEX_ID`, `YC_ASSISTANT_ID` — появятся после выполнения `ingest_yc.py` и `create_assistant.py`.
- `MANAGED_RAG_*` — пустые до тех пор, пока не станет доступен публичный URL Responses API/Managed RAG.

### Managed RAG (Responses API)
Пока публичный URL Managed RAG (`ai-factory.api.cloud.yandex.net`) недоступен, оставьте поля `MANAGED_RAG_PUBLIC_URL`, `MANAGED_RAG_VERSION_ID`, `MANAGED_RAG_TOKEN` пустыми в `.env`. Как только URL появится, получите `publicUrl` и `version` через API или консоль и создайте секрет:

```
yc secrets create --name MANAGED_RAG_TOKEN --data accessToken=<token>
```

Добавьте данные в `.env` (или в GitHub Secrets): `MANAGED_RAG_PUBLIC_URL=<url>`, `MANAGED_RAG_VERSION_ID=<version>`, `MANAGED_RAG_TOKEN=<secret>` и опишите эти переменные в документации. Код в `responses_client.py` автоматически переключится на `retrieve_generate`, если все три заполнены.

## 2. Сборка и публикация контейнера
1. Локально соберите образ:

```
docker build -t ghcr.io/<ваш-репозиторий>/telegram-ai-bot:latest .
```

2. Войдите в GitHub Container Registry или Yandex Container Registry и запушьте образ:

```
docker push ghcr.io/<ваш-репозиторий>/telegram-ai-bot:latest
```

3. Задеплойте Serverless Container:

```
yc serverless-container deploy \
  --name telegram-ai-bot \
  --memory 1GiB \
  --concurrency 1 \
  --image ghcr.io/<ваш-репозиторий>/telegram-ai-bot:latest \
  --env DATABASE_URL=<postgres url> \
  --env YANDEX_FOLDER_ID=<folder id> \
  --secrets TELEGRAM_BOT_TOKEN,YC_API_KEY,YC_FOLDER_ID,YC_OBS_ACCESS_KEY_ID,YC_OBS_SECRET_ACCESS_KEY
```

Если вы используете Managed PostgreSQL, замените `DATABASE_URL` на `postgresql://<user>:<pass>@<managed host>:5432/ai_bot`. Дополнительно можно передать `YC_OBS_REGION`, `YC_OBS_BUCKET` и `YC_OBS_PREFIX` напрямую или тоже сделать их секретами.

## 3. Работа с базой знаний
1. Загрузите файлы в Object Storage в `processoff-kb/knowledge-base/`.
2. Запустите `python ingest_yc.py` — он создаст Search Index, сохранит его ID в `.yc_search_index_id` и обновит `.env`.
3. Создайте ассистента через `python create_assistant.py`, это запишет `YC_ASSISTANT_ID` и `YC_ASSISTANT_NAME`.

В контейнере можно запускать те же команды вручную или привязать их к отдельному CI job (например, GitHub Actions Job `ingest`), чтобы обновления происходили автоматически.

## 4. Управление Managed RAG после появления API
1. Получите `publicUrl` и `version` через `curl` к `ai-factory.api.cloud.yandex.net/ai-factory/v1/knowledge-bases` (когда DNS перестанет быть недоступен).
2. Обновите `.env` и секреты `MANAGED_RAG_*`.
3. `responses_client.py` будет использовать `retrieve_generate`, а не локальный Search Index.

## 5. Поддержка минимального расхода токенов
- Используйте `.env.local` для локальной разработки, указывая только необходимые ключи.
- Не отправляйте всю историю треда в модель: настройте `MANAGED_RAG` инструкции, чтобы обращаться к базе только при явной просьбе, как показано в примерах Yandex (см. `instruction` из `create_assistant.py`).
- Привязывайте обновления Search Index только к новым файлам или редким событиям, чтобы не перегружать API. Скрипты `diag_connectivity.py` и `check_kb_data.py` помогут мониторить состояние.

Перед деплоем выполните python check_env.py --env .env --env .env.prod, чтобы убедиться, что все критичные значения присутствуют.
\nДля полного CI/CD контура внутри Yandex Cloud (DevTools Repo, Cloud Build, Cloud Deploy, Lockbox) см. файл Yandex_DEVOPS.md.\n\nИнструкции по автоматизации ingestion/diag job’ов см. в Yandex_AUTOMATION.md.\n## Настройка Serverless Container в Yandex Cloud
1. Создайте сервисный аккаунт, который будет выполнять запросы от имени контейнера:
   `
   yc iam service-account create --name telegram-bot-sa
   yc resource-manager folder add-access-binding \
     --id <folder-id> \
     --role serverless.containers.invoker \
     --subject serviceAccount:<sa-id>
   yc resource-manager folder add-access-binding \
     --id <folder-id> \
     --role lockbox.payloadViewer \
     --subject serviceAccount:<sa-id>
   `
2. Создайте контейнер (если не создан ранее):
   `
   yc serverless container create \
     --name telegram-ai-bot \
     --description "ProcessOff telegram bot" \
     --service-account-id <sa-id>
   `
3. Разверните ревизию с указанием образа и переменных:
   `
   yc serverless container revision deploy \
     --container-name telegram-ai-bot \
     --image cr.yandex/<registry-id>/telegram-ai-bot:<tag> \
     --execution-timeout 30s \
     --concurrency 1 \
     --cores 1 \
     --memory 1GiB \
     --env DATABASE_URL=postgresql://... \
     --env YANDEX_FOLDER_ID=<folder-id> \
     --secrets TELEGRAM_BOT_TOKEN=<secret-id>:TELEGRAM_BOT_TOKEN,YC_API_KEY=<secret-id>:YC_API_KEY,YC_OBS_ACCESS_KEY_ID=<secret-id>:YC_OBS_ACCESS_KEY_ID,YC_OBS_SECRET_ACCESS_KEY=<secret-id>:YC_OBS_SECRET_ACCESS_KEY
   `
4. Проверьте ревизию и статус endpoint:
   `
   yc serverless container revision list --name telegram-ai-bot
   yc serverless container get --name telegram-ai-bot
   `
   Когда endpoint активен, настройте вебхук Telegram (если используете вебхук):
   `
   curl -X POST "https://api.telegram.org/bot/setWebhook" -d "url=https://<public-endpoint>/webhook"
   `
5. Настройте Managed PostgreSQL (если ещё не сделали):
   `
   yc managed-postgresql cluster create ...
   yc managed-postgresql database create ...
   yc managed-postgresql user create --grants ddl,db_datawriter,db_datareader ...
   `
   Не забудьте открыть доступ в security group и обновить DATABASE_URL.
6. После релиза нового образа повторяйте шаг 3 (yc serverless container revision deploy) или автоматизируйте через Cloud Deploy.

Перед повторными выкладками проверяйте переменные командой python check_env.py --env .env --env .env.prod, чтобы избежать несовпадений между локальными файлами и Lockbox.
### Cloud Deploy ����������
- ������ ������������: deploy-spec.yaml (�������� container-id, Lockbox secretId, service accounts).
- ������� ��� �������� ��������� ��������� � ������ ����� �������� � Yandex_DEVOPS.md (������ ���������� �������� � ����).
- � .cloudbuild.yaml �������� _REGISTRY, _DEPLOY_SPEC, _DEPLOY_SA � ��������� ���� � DevTools Repo.

