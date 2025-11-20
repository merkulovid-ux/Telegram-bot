# Managed PostgreSQL (Cloud.ru)

## Обзор сервиса
Cloud.ru предоставляет полностью управляемый PostgreSQL сервис с поддержкой pgvector для векторных операций.

## Ключевые возможности
- PostgreSQL версии: 12, 13, 14, 15
- pgvector расширение для embeddings
- Высокая доступность (HA) с автоматическим failover
- Автоматическое резервное копирование
- Масштабирование ресурсов (CPU/память/диск)
- Мониторинг и алерты

## Создание кластера

### Через консоль
1. Перейти в раздел "Базы данных" → "PostgreSQL"
2. Нажать "Создать кластер"
3. Выбрать:
   - Регион (ru-moscow-1)
   - Версию PostgreSQL (15)
   - Тип инстанса (например, rds.pg.c6.large.2)
   - Размер диска (100-4000 GB)
   - Включить HA replication
4. Настроить сеть (VPC, подсеть, security group)
5. Создать пользователя admin

### Через Terraform
```hcl
resource "sbercloud_rds_instance_v3" "main" {
  name              = "telegram-ai-bot-pg"
  flavor            = "rds.pg.c6.large.2"
  ha_replication_mode = "async"
  volume {
    type = "ULTRAHIGH"
    size = 100
  }
  vpc_id            = var.vpc_id
  subnet_id         = var.subnet_id
  security_group_id = var.security_group_id
  availability_zone = "ru-moscow-1a"

  datastore {
    type    = "PostgreSQL"
    version = "15"
  }

  backup_strategy {
    start_time = "02:00-03:00"
    keep_days  = 7
  }

  parameters {
    name  = "shared_preload_libraries"
    value = "pgvector"
  }
}
```

## Управление пользователями

### Создание пользователей
```sql
-- Создание пользователя для приложения
CREATE USER app_user WITH PASSWORD 'strong_password';
GRANT ALL PRIVILEGES ON DATABASE ai_bot_db TO app_user;

-- Включение pgvector
CREATE EXTENSION IF NOT EXISTS vector;
```

### Terraform ресурс для пользователей
```hcl
resource "sbercloud_rds_database_privilege" "app_user" {
  instance_id = sbercloud_rds_instance_v3.main.id
  db_name     = "ai_bot_db"
  users {
    name     = "app_user"
    readonly = false
  }
}
```

## Миграция данных

### Подготовка
1. Создать дамп исходной базы:
   ```bash
   pg_dump -h source_host -U source_user -d source_db > dump.sql
   ```

2. Загрузить дамп в OBS бакет для временного хранения

3. Восстановить в Cloud.ru PostgreSQL:
   ```bash
   psql -h cloud_ru_host -U admin_user -d ai_bot_db < dump.sql
   ```

### Terraform подход
Использовать null_resource для автоматизации миграции:
```hcl
resource "null_resource" "db_migration" {
  depends_on = [sbercloud_rds_instance_v3.main]

  provisioner "local-exec" {
    command = "pg_restore -h ${sbercloud_rds_instance_v3.main.private_ips[0]} -U admin -d ai_bot_db dump.sql"
  }
}
```

## Мониторинг и обслуживание

### Метрики
- CPU/Memory/Disk usage
- Connections count
- Query performance
- Replication lag (для HA)

### Резервное копирование
- Автоматические бэкапы ежедневно
- Ручные снимки по требованию
- Восстановление на указанный момент времени

### Обновления
- Автоматическое применение патчей безопасности
- Ручное обновление версий PostgreSQL
- Maintenance windows

## Безопасность

### Сетевой доступ
- Private IP только (доступ через VPC)
- Security Groups для контроля трафика
- SSL/TLS шифрование соединений

### Аутентификация
- SCRAM-SHA-256 парольная аутентификация
- IAM интеграция для сервисных аккаунтов

## Ограничения и квоты
- Максимальный размер кластера: зависит от тарифа
- Максимальное количество подключений: зависит от конфигурации
- Резервные копии хранятся 7 дней по умолчанию

## API endpoints
- Management API: `https://rds.ru-moscow-1.hc.sbercloud.ru/v3/`
- Database connection: `postgresql://user:pass@host:5432/db`

## Troubleshooting
- Connection timeouts: проверить security groups
- pgvector не работает: убедиться в расширении
- Performance issues: мониторить метрики, увеличить ресурсы

## Ссылки
- [Managed PostgreSQL документация](https://cloud.ru/docs/cloud-databases/postgresql/concepts/about)
- [pgvector в PostgreSQL](https://github.com/pgvector/pgvector)
- [Terraform provider](https://registry.terraform.io/providers/sbercloud-terraform/sbercloud/latest)
