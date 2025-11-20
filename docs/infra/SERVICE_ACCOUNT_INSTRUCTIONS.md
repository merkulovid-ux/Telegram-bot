# Инструкции по созданию сервисных аккаунтов

Для автоматического развертывания и работы бота в Yandex Cloud необходимо создать три сервисных аккаунта с определенными ролями.

## 1. Создание сервисных аккаунтов

Вам нужно создать три сервисных аккаунта:

1.  `telegram-runtime`: для выполнения приложения (serverless container). ID: `ajeu8hlhoo3foji9h5tm`
2.  `telegram-deploy`: для развертывания контейнера. ID: `aje8dhdgluio1616q4e1`
3.  `telegram-build`: для сборки docker-образа в Cloud Build. ID: `ajegqhbg77skcnos1f83`

Создать их можно с помощью CLI или в веб-консоли Yandex Cloud.

**Пример создания с помощью CLI:**

```bash
yc iam service-account create --name telegram-runtime
yc iam service-account create --name telegram-deploy
yc iam service-account create --name telegram-build
```

## 2. Назначение ролей

Каждому сервисному аккаунту необходимо назначить определенные роли для доступа к ресурсам Yandex Cloud.

### 2.1. Роли для `telegram-runtime`

Этому аккаунту нужны права на работу с Yandex AI Studio, Object Storage и Lockbox.

```bash
# ID вашего сервисного аккаунта telegram-runtime
export RUNTIME_SA_ID=ajeu8hlhoo3foji9h5tm

# ID вашего каталога
export FOLDER_ID=$(yc config get folder-id)

# Назначение ролей
yc resource-manager folder add-access-binding --id $FOLDER_ID --role serverless.containers.invoker --service-account-id $RUNTIME_SA_ID
yc resource-manager folder add-access-binding --id $FOLDER_ID --role lockbox.payloadViewer --service-account-id $RUNTIME_SA_ID
yc resource-manager folder add-access-binding --id $FOLDER_ID --role ai.viewer --service-account-id $RUNTIME_SA_ID
yc resource-manager folder add-access-binding --id $FOLDER_ID --role storage.viewer --service-account-id $RUNTIME_SA_ID
```

### 2.2. Роли для `telegram-deploy`

Этому аккаунту нужны права на развертывание serverless-контейнеров.

```bash
# ID вашего сервисного аккаунта telegram-deploy
export DEPLOY_SA_ID=aje8dhdgluio1616q4e1

# Назначение ролей
yc resource-manager folder add-access-binding --id $FOLDER_ID --role serverless.containers.admin --service-account-id $DEPLOY_SA_ID
```

### 2.3. Роли для `telegram-build`

Этому аккаунту нужны права на сборку и загрузку docker-образов в Container Registry, а также на чтение секретов из Lockbox.

```bash
# ID вашего сервисного аккаунта telegram-build
export BUILD_SA_ID=ajegqhbg77skcnos1f83

# Назначение ролей
yc resource-manager folder add-access-binding --id $FOLDER_ID --role container-registry.images.pusher --service-account-id $BUILD_SA_ID
yc resource-manager folder add-access-binding --id $FOLDER_ID --role lockbox.payloadViewer --service-account-id $BUILD_SA_ID
```

## 3. Использование в `deploy-spec.yaml`

После создания сервисного аккаунта `telegram-runtime` вам нужно будет указать его ID в файле `deploy-spec.yaml` в поле `service-account-id`.

```yaml
# ...
spec:
  containers:
    - name: app
      # ...
      service-account-id: ajeu8hlhoo3foji9h5tm
      # ...
```
