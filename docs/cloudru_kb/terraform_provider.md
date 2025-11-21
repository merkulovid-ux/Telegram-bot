# Terraform Provider для Cloud.ru

## Обзор
SberCloud Terraform Provider позволяет управлять инфраструктурой Cloud.ru через код.

## Установка и настройка

### Требования
- Terraform >= 1.5.0
- Go >= 1.18 (для сборки из исходников)

### Установка провайдера
```hcl
terraform {
  required_providers {
    sbercloud = {
      source  = "sbercloud-terraform/sbercloud"
      version = ">= 1.14.0"
    }
  }
}
```

### Аутентификация
```hcl
provider "sbercloud" {
  access_key = var.access_key
  secret_key = var.secret_key
  region     = "ru-moscow-1"
}
```

## Основные ресурсы

### VPC и сеть
```hcl
# VPC
resource "sbercloud_vpc" "main" {
  name = "telegram-ai-bot-vpc"
  cidr = "10.20.0.0/16"
}

# Подсеть
resource "sbercloud_vpc_subnet" "app" {
  vpc_id      = sbercloud_vpc.main.id
  name        = "app-subnet"
  cidr        = "10.20.1.0/24"
  gateway_ip  = "10.20.1.1"
  primary_dns = "100.125.0.41"
}

# Security Group
resource "sbercloud_networking_secgroup" "app" {
  name        = "telegram-ai-bot-sg"
  description = "Security group for Telegram bot"
}

resource "sbercloud_networking_secgroup_rule" "allow_http" {
  security_group_id = sbercloud_networking_secgroup.app.id
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 80
  port_range_max    = 80
  remote_ip_prefix  = "0.0.0.0/0"
}
```

### Object Storage (OBS)
```hcl
# OBS бакет
resource "sbercloud_obs_bucket" "terraform_state" {
  bucket = "telegram-ai-bot-tfstate"
  region = "ru-moscow-1"

  versioning {
    enabled = true
  }

  # Bucket policy
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          SberCloud = "52b69061-6b4e-4ca9-9446-0d619feb3d31"
        }
        Action = [
          "obs:GetObject",
          "obs:PutObject",
          "obs:DeleteObject",
          "obs:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::telegram-ai-bot-tfstate",
          "arn:aws:s3:::telegram-ai-bot-tfstate/*"
        ]
      }
    ]
  })
}
```

### Managed PostgreSQL
```hcl
resource "sbercloud_rds_instance_v3" "postgresql" {
  name              = "telegram-ai-bot-pg"
  flavor            = "rds.pg.c6.large.2"
  ha_replication_mode = "async"

  volume {
    type = "ULTRAHIGH"
    size = 100
  }

  vpc_id            = sbercloud_vpc.main.id
  subnet_id         = sbercloud_vpc_subnet.app.id
  security_group_id = sbercloud_networking_secgroup.app.id
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

# База данных
resource "sbercloud_rds_database" "app_db" {
  instance_id = sbercloud_rds_instance_v3.postgresql.id
  name        = "ai_bot_db"
  character_set = "UTF8"
}

# Пользователь
resource "sbercloud_rds_database_privilege" "app_user" {
  instance_id = sbercloud_rds_instance_v3.postgresql.id
  db_name     = "ai_bot_db"
  users {
    name     = "app_user"
    readonly = false
  }
}
```

### Container Apps
```hcl
# Environment
resource "sbercloud_apig_environment" "container_env" {
  name        = "telegram-ai-bot-env"
  description = "Container environment for Telegram bot"

  vpc_id     = sbercloud_vpc.main.id
  subnet_ids = [sbercloud_vpc_subnet.app.id]
}

# Instance
resource "sbercloud_apig_instance" "container_instance" {
  environment_id = sbercloud_apig_environment.container_env.id

  instance_config {
    specification  = "PROFESSIONAL"
    instance_count = 1
  }
}

# API Gateway
resource "sbercloud_apig_api" "webhook" {
  environment_id = sbercloud_apig_environment.container_env.id
  instance_id    = sbercloud_apig_instance.container_instance.id

  name        = "telegram-webhook"
  description = "Telegram webhook endpoint"

  request_protocol = "HTTPS"
  request_method   = "POST"
  request_uri      = "/webhook"

  backend_type    = "HTTP"
  backend_address = "http://telegram-ai-bot.internal:8080"
}
```

## Backend configuration

### OBS backend
```hcl
terraform {
  backend "s3" {
    bucket   = "telegram-ai-bot-tfstate"
    key      = "terraform/state"
    region   = "ru-moscow-1"
    endpoint = "https://obs.ru-moscow-1.hc.sbercloud.ru"

    skip_credentials_validation = true
    skip_region_validation      = true
    skip_requesting_account_id  = true

    access_key = "your_access_key"
    secret_key = "your_secret_key"
  }
}
```

## Data sources

### Получение информации о существующих ресурсах
```hcl
data "sbercloud_vpc" "existing" {
  name = "existing-vpc-name"
}

data "sbercloud_obs_bucket" "state" {
  bucket = "telegram-ai-bot-tfstate"
}
```

## Best practices

### Структура проекта
```
terraform/
├── main.tf           # Основные ресурсы
├── variables.tf      # Переменные
├── outputs.tf        # Выходы
├── terraform.tfvars  # Значения переменных
├── backend.hcl       # Backend config
└── modules/          # Переиспользуемые модули
    ├── network/
    ├── database/
    └── storage/
```

### Управление секретами
```hcl
# Не хранить секреты в коде!
variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

# Использовать Vault или GitHub Secrets
```

### Теги и организация
```hcl
locals {
  common_tags = {
    Project     = "telegram-ai-bot"
    Environment = var.environment
    ManagedBy   = "terraform"
    Owner       = "team"
  }
}

resource "sbercloud_vpc" "main" {
  # ...
  tags = local.common_tags
}
```

## Ограничения и known issues

### Поддержка ресурсов
- Не все сервисы Cloud.ru имеют Terraform ресурсы
- Некоторые параметры могут быть недоступны
- API может изменяться

### Аутентификация
- Access keys имеют ограниченный срок действия
- Рекомендуется ротировать ключи регулярно
- Использовать service accounts вместо user accounts

## Troubleshooting

### Common errors
- `Error: Invalid credentials`: проверить access_key/secret_key
- `Error: Resource not found`: проверить region и resource IDs
- `Error: Quota exceeded`: проверить лимиты аккаунта

### Debug commands
```bash
# Validate configuration
terraform validate

# Plan changes
terraform plan

# Show state
terraform show

# Debug API calls
TF_LOG=DEBUG terraform apply
```

## Обновления и поддержка

### Версии
- Провайдер активно развивается
- Проверять compatibility с Terraform версиями
- Следить за release notes

### Community
- GitHub issues для багрепортов
- Documentation updates
- Examples и templates

## Ссылки
- [Terraform Registry](https://registry.terraform.io/providers/sbercloud-terraform/sbercloud/latest)
- [GitHub Repository](https://github.com/sbercloud-terraform/terraform-provider-sbercloud)
- [Documentation](https://cloud.ru/docs/terraform/concepts/about)

