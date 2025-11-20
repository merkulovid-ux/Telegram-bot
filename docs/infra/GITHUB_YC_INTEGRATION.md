# Интеграция GitHub с Yandex Cloud: Пошаговое руководство

Это руководство описывает лучшие практики для интеграции вашего GitHub-репозитория с Yandex Cloud для автоматизации CI/CD процессов.

## 1. Аутентификация с помощью федерации удостоверений (Workload Identity Federation)

Это наиболее безопасный способ аутентификации GitHub Actions в Yandex Cloud без хранения долгосрочных секретов в GitHub.

1.  **Создайте федерацию удостоверений в Yandex Cloud:**
    ```bash
    yc iam federation create --name "github-federation" \
      --description "Federation for GitHub Actions" \
      --issuer "https://token.actions.githubusercontent.com" \
      --subject-type "repo"
    ```

2.  **Добавьте сертификат федерации:**
    ```bash
    yc iam federation certificate create --federation-name "github-federation" \
      --url "https://token.actions.githubusercontent.com/.well-known/jwks"
    ```

3.  **Создайте сервисный аккаунт** (если еще не создан), который будет использоваться GitHub Actions:
    ```bash
    yc iam service-account create --name "github-actions-sa"
    ```

4.  **Назначьте сервисному аккаунту необходимые роли.** Например, для сборки и развертывания контейнера:
    ```bash
    export SA_ID=$(yc iam service-account get --name "github-actions-sa" --format json | jq -r .id)
    export FOLDER_ID=$(yc config get folder-id)

    yc resource-manager folder add-access-binding --id $FOLDER_ID --role container-registry.images.pusher --service-account-id $SA_ID
    yc resource-manager folder add-access-binding --id $FOLDER_ID --role serverless.containers.editor --service-account-id $SA_ID
    yc resource-manager folder add-access-binding --id $FOLDER_ID --role lockbox.payloadViewer --service-account-id $SA_ID
    ```

5.  **Разрешите сервисному аккаунту использовать федерацию:**
    ```bash
    yc iam federation add-user-account --federation-name "github-federation" \
      --subject "repo:<your-github-org>/<your-repo>:ref:refs/heads/main" \
      --service-account-id $SA_ID
    ```
    Замените `<your-github-org>/<your-repo>` на ваш репозиторий.

## 2. CI/CD с GitHub Actions

Создайте workflow-файл в вашем репозитории по пути `.github/workflows/deploy.yml`.

```yaml
name: Deploy to Yandex Cloud

on:
  push:
    branches:
      - main

jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: read

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Authenticate to Yandex Cloud
        uses: yandex-cloud/auth-action@v1
        with:
          federation_id: <your-federation-id>
          sa_id: <your-service-account-id>

      - name: Login to Yandex Container Registry
        uses: docker/login-action@v2
        with:
          registry: cr.yandex
          username: oauth
          password: ${{ steps.auth.outputs.yc-token }}

      - name: Build and push Docker image
        run: |
          docker build -t cr.yandex/<your-registry-id>/telegram-ai-bot:${{ github.sha }} .
          docker push cr.yandex/<your-registry-id>/telegram-ai-bot:${{ github.sha }}

      - name: Deploy Serverless Container
        uses: yandex-cloud/serverless-containers-deploy@v1
        with:
          container_id: <your-container-id>
          image_url: cr.yandex/<your-registry-id>/telegram-ai-bot:${{ github.sha }}
          service_account_id: <your-runtime-service-account-id>
          secrets: |
            TELEGRAM_BOT_TOKEN=${{ secrets.LOCKBOX_SECRET_ID }}:TELEGRAM_BOT_TOKEN
            YC_API_KEY=${{ secrets.LOCKBOX_SECRET_ID }}:YC_API_KEY
          environment: |
            DATABASE_URL=${{ secrets.DATABASE_URL }}
            YANDEX_FOLDER_ID=<your-folder-id>
```

## 3. Управление секретами

1.  **Создайте секрет в Yandex Lockbox** для хранения токенов и других конфиденциальных данных.
2.  **Добавьте ID секрета Lockbox в секреты GitHub** (`LOCKBOX_SECRET_ID`).
3.  **Используйте `secrets` в GitHub Actions** для безопасной передачи секретов в ваше приложение.

Это руководство предоставляет основу для безопасной и эффективной интеграции. Вы можете адаптировать его под свои конкретные нужды, добавляя шаги для тестирования, статического анализа и других проверок качества.

## 4. Предлагаемые архитектурные улучшения

Для создания более мощного и надежного AI-агента, мы предлагаем следующие улучшения, основанные на современных практиках:

-   **Внедрение `LangGraph`**: Для создания структурированных и масштабируемых агентских рабочих процессов.
-   **Улучшение управления памятью с `mem0`**: Для обеспечения долговременной памяти и персонализации.
-   **Улучшение мониторинга**: Внедрение структурированного логирования для лучшей отладки и анализа.
-   **Оптимизация RAG**: Использование техник контекстного сжатия для повышения релевантности и эффективности.

Подробное описание этих улучшений находится в файле `ARCHITECTURAL_IMPROVEMENTS.md`.
