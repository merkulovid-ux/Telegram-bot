terraform {
  required_version = ">= 1.5.0"

  required_providers {
    sbercloud = {
      source  = "sbercloud-terraform/sbercloud"
      version = ">= 1.0.0"
    }
  }
}

locals {
  project     = "telegram-ai-bot"
  environment = var.environment
  region      = var.cloud_ru_region

  default_tags = {
    Project     = local.project
    Environment = local.environment
    ManagedBy   = "terraform"
  }
}

provider "sbercloud" {
  access_key = var.sbercloud_access_key
  secret_key = var.sbercloud_secret_key
  region     = local.region
}

variable "sbercloud_access_key" {
  description = "Cloud.ru (SberCloud) Access Key для сервисного аккаунта Terraform."
  type        = string
  sensitive   = true
}

variable "sbercloud_secret_key" {
  description = "Cloud.ru (SberCloud) Secret Key для сервисного аккаунта Terraform."
  type        = string
  sensitive   = true
}

variable "cloud_ru_region" {
  description = "Регион Cloud.ru, в котором создаются ресурсы."
  type        = string
  default     = "ru-moscow-1"
}

variable "environment" {
  description = "Имя окружения (dev/stage/prod) для тегов и изоляции ресурсов."
  type        = string
  default     = "dev"
}

variable "network_vpc_name" {
  description = "Имя VPC для Cloud.ru."
  type        = string
  default     = "telegram-ai-bot"
}

variable "network_vpc_cidr" {
  description = "CIDR блок для VPC."
  type        = string
  default     = "10.20.0.0/16"
}

variable "network_subnets" {
  description = "Подсети, которые будут созданы в разных зонах доступности."
  type = list(object({
    name              = string
    cidr              = string
    gateway_ip        = string
    availability_zone = string
  }))
  default = [
    {
      name              = "app-a"
      cidr              = "10.20.1.0/24"
      gateway_ip        = "10.20.1.1"
      availability_zone = "ru-moscow-1a"
    },
    {
      name              = "app-b"
      cidr              = "10.20.2.0/24"
      gateway_ip        = "10.20.2.1"
      availability_zone = "ru-moscow-1b"
    }
  ]
}

variable "network_security_group_name" {
  description = "Имя security group по умолчанию."
  type        = string
  default     = "telegram-ai-bot-sg"
}

variable "network_security_group_description" {
  description = "Описание security group по умолчанию."
  type        = string
  default     = "Default SG for Telegram AI Bot workloads."
}

variable "network_security_group_rules" {
  description = "Ingress правила для security group."
  type = list(object({
    protocol         = string
    port_range_min   = number
    port_range_max   = number
    remote_ip_prefix = string
    description      = string
  }))
  default = [
    {
      protocol         = "tcp"
      port_range_min   = 80
      port_range_max   = 80
      remote_ip_prefix = "0.0.0.0/0"
      description      = "Allow HTTP"
    },
    {
      protocol         = "tcp"
      port_range_min   = 443
      port_range_max   = 443
      remote_ip_prefix = "0.0.0.0/0"
      description      = "Allow HTTPS"
    }
  ]
}

variable "pg_version" {
  description = "Версия PostgreSQL для managed кластера."
  type        = string
  default     = "15"
}

variable "pg_volume_size" {
  description = "Размер диска для PostgreSQL в GB."
  type        = number
  default     = 100
}

variable "pg_admin_user" {
  description = "Имя администратора базы данных."
  type        = string
  default     = "pg_admin"
}

module "network" {
  source = "./modules/network"

  vpc_name   = var.network_vpc_name
  vpc_cidr   = var.network_vpc_cidr
  subnets    = var.network_subnets

  security_group_name        = var.network_security_group_name
  security_group_description = var.network_security_group_description
  security_group_rules       = var.network_security_group_rules
}

module "managed_pg" {
  source = "./modules/managed_pg"

  vpc_id            = module.network.vpc_id
  subnet_id         = module.network.private_subnet_id
  security_group_id = module.network.database_sg_id
  app_subnet_cidr   = module.network.app_subnet_cidr

  environment = var.environment
  pg_version  = var.pg_version
  volume_size = var.pg_volume_size
  db_admin_user = var.pg_admin_user
}

# TODO: добавить модули
# - Object Storage (OBS) для базы знаний и terraform state
# - Vault (секреты)
# - Container Apps для Telegram Bot
# - Artifact Registry
