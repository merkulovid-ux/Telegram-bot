# Managed PostgreSQL Module

Этот модуль создаёт кластер Cloud.ru Managed PostgreSQL с поддержкой pgvector для хранения embeddings и данных Telegram-бота.

## Требования

- Сервисный аккаунт Cloud.ru с правами на создание RDS-инстансов и управление сетью.
- VPC и подсеть из модуля `network`.
- Vault для хранения паролей (не храните пароли в Terraform state!).

## Переменные

### Обязательные
- `vpc_id` — ID VPC
- `subnet_id` — ID приватной подсети
- `security_group_id` — ID Security Group
- `app_subnet_cidr` — CIDR подсети приложения для правил доступа

### Опциональные
- `pg_version` — версия PostgreSQL (по умолчанию 15)
- `instance_flavor` — тип инстанса (по умолчанию `rds.pg.c6.large.2`)
- `volume_size` — размер диска в GB (100-4000)
- `db_admin_user` — имя админа (по умолчанию `pg_admin`)
- `environment` — окружение (dev/stage/prod)

## Выходы (Outputs)

- `cluster_id` — ID кластера
- `db_endpoint` — приватный IP-адрес
- `db_name` — имя базы данных
- `db_admin_user` — имя пользователя
- `vault_secret_path` — путь к секрету в Vault
- `db_connection_template` — шаблон строки подключения

## Пример использования

```hcl
module "managed_pg" {
  source = "./modules/managed_pg"

  vpc_id             = module.network.vpc_id
  subnet_id          = module.network.private_subnet_id
  security_group_id  = module.network.database_sg_id
  app_subnet_cidr    = module.network.app_subnet_cidr
  environment        = var.environment
}
```

## Управление паролями

Пароли хранятся в Cloud.ru Vault (не в Terraform!):
1. Создайте секрет `/v1/secret/data/pg_credentials`
2. Добавьте ключ `password` с сгенерированным паролем
3. В коде приложения читайте пароль из Vault

## Миграция данных

После создания кластера:
1. Сделайте pg_dump старой базы
2. Загрузите dump в OBS-бакет
3. Восстановите через `pg_restore` или SQL

## Безопасность

- Кластер доступен только из внутренней сети VPC
- Пароли не хранятся в Terraform state
- Включены automated backups
- Поддержка pgvector для embeddings
