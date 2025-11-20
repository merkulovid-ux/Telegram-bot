# Cloud.ru Knowledge Base

База знаний по документации Cloud.ru для миграции Telegram AI Bot.

## Структура изучения

### 1. IAM & Service Accounts (Приоритет: Высокий)
- Управление пользователями и ролями
- Сервисные аккаунты и ключи доступа
- IAM API и аутентификация
- **[Документация](../infra/SBERCLOUD_CREDENTIALS_GUIDE_V2.md)**

### 2. Object Storage (OBS/S3) (Приоритет: Высокий)
- Создание и управление бакетами
- Политики доступа и права
- API и SDK интеграция
- Terraform backend setup
- **[Документация](https://cloud.ru/docs/s3e/ug/index)**

### 3. Managed PostgreSQL (Приоритет: Высокий)
- Создание кластеров
- Настройка pgvector
- Миграция данных
- Безопасность и доступ
- **[Документация](managed_postgresql.md)**

### 4. Container Apps (Приоритет: Высокий)
- Развертывание Docker-контейнеров
- Автомасштабирование
- Секреты и переменные окружения
- Интеграция с CI/CD
- **[Документация](container_apps.md)**

### 5. Networking & VPC (Приоритет: Средний)
- Виртуальные сети
- Security Groups
- Подсети и availability zones
- **[Terraform модуль](../terraform/modules/network/)**

### 6. Terraform & IaC (Приоритет: Высокий)
- Провайдеры Cloud.ru
- Модули и ресурсы
- Backend configuration
- Best practices
- **[Документация](terraform_provider.md)**

### 7. CI/CD Integration (Приоритет: Средний)
- GitHub Actions
- Artifact Registry
- Автоматизированные деплой
- **[Workflow](../.github/workflows/infra-cloudru.yml)**

### 8. Security & Vault (Приоритет: Высокий)
- Управление секретами
- Шифрование
- Аудит и мониторинг

### 9. Migration Planning
- Комплексный план миграции
- Чеклисты и риски
- Timeline и ресурсы
- **[Чеклист](migration_checklist.md)**

## Формат хранения

Каждый раздел содержит:
- Ключевые понятия и термины
- API endpoints и методы
- Примеры кода/SDK
- Terraform ресурсы
- Best practices и ограничения
- Ссылки на официальную документацию

## Текущий статус изучения

- [x] IAM & Service Accounts (базовые знания + практические ключи)
- [x] OBS/S3 (bucket policies, access keys, Terraform backend)
- [x] Managed PostgreSQL (API, Terraform ресурсы, миграция данных)
- [x] Container Apps (развертывание, масштабирование, секреты)
- [x] Terraform provider (ресурсы, аутентификация, best practices)
- [x] Migration checklist (комплексный план миграции)
- [ ] CI/CD integration (нужно детальное изучение)
- [ ] Vault/Secrets (нужно изучение API)
- [ ] Monitoring & Alerting (нужно изучение)

## Следующие шаги

1. Изучить Managed PostgreSQL API и Terraform ресурсы
2. Документировать Container Apps для деплоя
3. Проверить Terraform provider compatibility
4. Составить чеклист миграции по всем сервисам
