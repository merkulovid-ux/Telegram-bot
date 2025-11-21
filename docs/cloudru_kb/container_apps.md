# Container Apps (Cloud.ru)

## Обзор сервиса
Container Apps - это бессерверная платформа для запуска Docker-контейнеров в Cloud.ru с автоматическим масштабированием.

## Ключевые возможности
- Запуск Docker-контейнеров без управления серверами
- Автомасштабирование от 0 до N инстансов
- Интеграция с Artifact Registry
- Управление секретами через Vault
- HTTP/HTTPS endpoints с автоматическими сертификатами
- Мониторинг и логирование

## Создание приложения

### Через консоль
1. Перейти в "Container Apps" → "Приложения"
2. Нажать "Создать приложение"
3. Выбрать:
   - Имя приложения
   - Регион (ru-moscow-1)
   - Artifact Registry образ
4. Настроить:
   - CPU/память (минимум/максимум)
   - Масштабирование (concurrency, min/max instances)
   - Переменные окружения
   - Секреты из Vault
   - Порты и протоколы

### Через Terraform
```hcl
resource "sbercloud_apig_environment" "container_app" {
  name        = "telegram-ai-bot"
  description = "Telegram AI Bot container application"

  vpc_id = var.vpc_id
  subnet_ids = var.subnet_ids
}

resource "sbercloud_apig_instance" "app_instance" {
  environment_id = sbercloud_apig_environment.container_app.id

  instance_config {
    specification = "PROFESSIONAL"
    instance_count = 1
  }
}

resource "sbercloud_apig_api" "telegram_bot_api" {
  environment_id = sbercloud_apig_environment.container_app.id
  instance_id    = sbercloud_apig_instance.app_instance.id

  name        = "telegram-webhook"
  description = "Telegram webhook endpoint"

  request_protocol = "HTTPS"
  request_method   = "POST"
  request_uri      = "/webhook"

  backend_type = "HTTP"
  backend_address = "http://container-app.internal:8080"

  # Authentication and other settings
}
```

## Развертывание образов

### Artifact Registry
1. Создать registry: `telegram-ai-bot-repo`
2. Загрузить Docker образ:
   ```bash
   docker tag my-app gcr.io/project-id/telegram-ai-bot-repo:latest
   docker push gcr.io/project-id/telegram-ai-bot-repo:latest
   ```
3. Указать образ в Container Apps

### CI/CD интеграция
```yaml
# .github/workflows/deploy.yml
- name: Build and push Docker image
  run: |
    docker build -t gcr.io/${{ secrets.GCR_PROJECT }}/telegram-ai-bot:${{ github.sha }} .
    docker push gcr.io/${{ secrets.GCR_PROJECT }}/telegram-ai-bot:${{ github.sha }}

- name: Deploy to Container Apps
  run: |
    # Use Cloud.ru CLI or API to update container app
    curl -X POST https://container-apps.ru-moscow-1.hc.sbercloud.ru/v1/apps/${APP_ID}/deploy \
      -H "Authorization: Bearer ${{ secrets.CLOUDRU_TOKEN }}" \
      -d '{"image": "gcr.io/project/telegram-ai-bot:${{ github.sha }}"}'
```

## Управление секретами

### Через Vault
1. Создать секреты в Vault:
   - `telegram_bot_token`
   - `database_url`
   - `openai_api_key`

2. Привязать к Container App:
   ```hcl
   resource "sbercloud_apig_api" "with_secrets" {
     # ... other config

     backend_params {
       name  = "TELEGRAM_BOT_TOKEN"
       value = "vault://secret/telegram_bot_token"
     }
   }
   ```

### Переменные окружения
```hcl
resource "sbercloud_apig_environment_variable" "db_url" {
  environment_id = sbercloud_apig_environment.container_app.id
  name          = "DATABASE_URL"
  value         = var.database_url
}
```

## Масштабирование

### Автоматическое
- **Concurrency**: максимум одновременных запросов на инстанс
- **Min/Max instances**: диапазон масштабирования
- **CPU/Memory thresholds**: триггеры для увеличения

### Ручное
Через API или консоль можно установить фиксированное количество инстансов.

## Мониторинг

### Метрики
- CPU/Memory usage
- Request count/rate
- Response times
- Error rates
- Instance count

### Логи
- Application logs
- System logs
- Access logs
- Интеграция с Cloud.ru Logging

## Безопасность

### Сетевой уровень
- Private networking через VPC
- Security Groups
- HTTPS-only endpoints

### Аутентификация
- API keys для доступа
- JWT tokens
- Integration с IAM

### Секреты
- Шифрование at-rest
- Secure access from Vault
- No secrets in environment variables

## Ограничения
- Максимум 100 инстансов на приложение
- CPU: 0.1-16 cores
- Memory: 128MB-32GB
- Timeout: 30 секунд на запрос
- Cold start latency при масштабировании до 0

## Troubleshooting

### Common issues
- **Cold start delays**: увеличить min instances
- **Memory limits**: мониторить и увеличивать allocation
- **Network timeouts**: проверить security groups
- **Image pull failures**: проверить Artifact Registry access

### Debug commands
```bash
# Check app status
curl -H "Authorization: Bearer $TOKEN" \
  https://container-apps.ru-moscow-1.hc.sbercloud.ru/v1/apps/$APP_ID

# View logs
curl -H "Authorization: Bearer $TOKEN" \
  https://container-apps.ru-moscow-1.hc.sbercloud.ru/v1/apps/$APP_ID/logs
```

## Ссылки
- [Container Apps документация](https://cloud.ru/docs/container-apps/concepts/about)
- [Artifact Registry](https://cloud.ru/docs/artifacts/concepts/about)
- [Terraform provider](https://registry.terraform.io/providers/sbercloud-terraform/sbercloud/latest)


