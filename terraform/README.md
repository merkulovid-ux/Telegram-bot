# Terraform — Cloud.ru Bootstrap

Этот каталог содержит инфраструктурный код для миграции Telegram AI Bot на Cloud.ru (см. `docs/infra/SBERCLOUD_MIGRATION_PLAN.md`). Ниже — чеклист для DevOps/Architect ролей.

## 1. Предварительные требования
1. Получите сервисный аккаунт Cloud.ru с ролью `admin`/`infra-admin` (см. `docs/infra/SBERCLOUD_CREDENTIALS_GUIDE_V2.md`).
2. Создайте отдельный OBS-бакет для хранения Terraform state (можно вручную через консоль).
3. Сгенерируйте Access Key / Secret Key и сохраните их в Vault/Lockbox (не коммитим в репозиторий).
4. Установите Terraform >= 1.5.0.

## 2. Настройка backend
1. Скопируйте `backend.hcl.example` в `backend.hcl` и подставьте реальные значения (имя OBS-бакета, ключ state, endpoint).
2. OBS использует S3-протокол. Для `terraform init` выполняйте:
   ```bash
   terraform init -backend-config=backend.hcl
   ```
3. Флаг `skip_*` обязателен: OBS не поддерживает все проверки AWS S3 SDK.

## 3. Конфигурация переменных
1. Скопируйте `terraform.tfvars.example` в `terraform.tfvars` или `env.auto.tfvars`.
2. Укажите реальные `sbercloud_access_key`, `sbercloud_secret_key`, `cloud_ru_region`, `environment`.
3. Файл `terraform.tfvars` игнорируется (`terraform/.gitignore`), храните его локально или в CI/CD секретах.

## 4. Развитие модулей
Планируемые модули (см. `docs/infra/SBERCLOUD_MIGRATION_PLAN.md`):

| Модуль | Ресурсы | Ответственный |
| --- | --- | --- |
| `network` | VPC, сабнеты, SecGroups | DevOps (реализовано) |
| `managed_pg` | Managed PostgreSQL с pgvector | DevOps + Backend (реализовано) |
| `storage` | OBS бакеты (ingest + state) | DevOps |
| `vault` | Secret Manager/Vault интеграция | DevOps |
| `container_apps` | Развёртывание Telegram Bot | DevOps + Backend |
| `ai_factory` | Managed RAG / GigaChat конфигурация | Backend |
| `monitoring` | Alerts, метрики, логирование | DevOps + QA |

В `main.tf` уже подключены модули `network` и `managed_pg` (см. `modules/network` и `modules/managed_pg`). Остальные модули добавляйте по мере проработки задач BL-15..BL-18 (см. `docs/process/BACKLOG.md`).

## 5. Workflow (TDD / XP)
1. **Red**: для каждого модуля готовим в tests/infra или smoke test (например, `terraform validate` + `terraform plan` в CI, unit-тесты через Terratest при необходимости).
2. **Green**: реализуем минимальную конфигурацию, чтобы тест прошёл.
3. **Refactor**: выносим общие locals/outputs, поддерживаем `default_tags`.
4. После каждого завершённого шага обновляем `docs/infra/SBERCLOUD_MIGRATION_PLAN.md` и фиксируем ретро-экшен (каждые 5 ответов).

## 6. Использование в CI/CD
1. GitHub Actions (`.github/workflows/infra-cloudru.yml`) выполняет `terraform fmt`, `init`, `validate`, `plan` при изменениях в каталоге `terraform/` или по `workflow_dispatch`.
2. Для работы пайплайн ожидает секреты:
   - `CLOUDRU_TF_BACKEND_HCL` — содержимое `backend.hcl` (OBS-бакет, endpoint, ключи).
   - `CLOUDRU_TFVARS` — значения `sbercloud_access_key`, `sbercloud_secret_key`, `cloud_ru_region`, `environment`.
3. Секреты хранятся в GitHub Secrets или Vault; при необходимости обновляйте их после ротации ключей.
4. Для `terraform apply` используйте отдельный workflow/manual run с ограниченными правами сервиса и дополнительным review.
5. Логи пайплайна подключайте к Monitoring (BL-18): ошибки Terraform → Alert/notification.

### Network (готово)

- модуль `modules/network` создаёт VPC, сабнеты и security group. Настраивается переменными `network_*` (см. `main.tf`, `terraform.tfvars.example`).
- Outputs (`vpc_id`, `subnet_ids`, `security_group_id`) будут использованы следующими модулями (БД, Container Apps, NAT).

## 7. Следующие шаги
- [ ] Создать OBS-бакет `telegram-ai-bot-tfstate` и зашифровать доступы в Vault.
- [x] Подготовить GitHub Actions workflow `infra-cloudru.yml`.
- [x] Реализовать модуль `network` (VPC + сабнеты) и smoke-тест.
- [ ] Обновить `docs/process/ROADMAP.md` статусом BL-15/BL-16.

Поддерживайте синхронизацию с Scrum Master/PO: все изменения отражаются в бэклоге, а результаты — в ретроспективах. Если требуются уточнения по API Cloud.ru, фиксируйте их как `spike` в `docs/process/BACKLOG.md`.

