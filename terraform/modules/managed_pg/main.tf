# Cloud.ru Managed PostgreSQL Module
# Creates a PostgreSQL cluster with pgvector support for embeddings storage

locals {
  # Common tags for resources
  default_tags = {
    Project     = "telegram-ai-bot"
    Environment = var.environment
    Component   = "database"
    ManagedBy   = "terraform"
  }

  # Derive cluster name and database name
  cluster_name = "${var.environment}-telegram-ai-bot-pg"
  db_name      = "ai_bot_db"
}

# Managed PostgreSQL cluster
resource "sbercloud_rds_instance_v3" "main" {
  name              = local.cluster_name
  flavor            = var.instance_flavor
  ha_replication_mode = var.ha_replication_mode  # e.g., "async"
  volume {
    type = var.volume_type  # e.g., "ULTRAHIGH"
    size = var.volume_size  # in GB
  }
  vpc_id            = var.vpc_id
  subnet_id         = var.subnet_id
  security_group_id = var.security_group_id
  availability_zone = var.availability_zone

  datastore {
    type    = "PostgreSQL"
    version = var.pg_version  # e.g., "12"
  }

  backup_strategy {
    start_time = "02:00-03:00"  # Daily backup window
    keep_days  = var.backup_keep_days
  }

  parameters {
    name  = "shared_preload_libraries"
    value = "pgvector"
  }

  parameters {
    name  = "max_connections"
    value = var.max_connections
  }

  # DB instance tags
  tags = local.default_tags
}

# Database within the cluster
resource "sbercloud_rds_database" "main" {
  instance_id = sbercloud_rds_instance_v3.main.id
  name        = local.db_name
  character_set = "UTF8"
}

# Database user (admin)
resource "sbercloud_rds_database_privilege" "admin" {
  instance_id = sbercloud_rds_instance_v3.main.id
  db_name     = sbercloud_rds_database.main.name
  users {
    name     = var.db_admin_user
    readonly = false
  }
}

# Security group rule for app access (allow from app subnet)
resource "sbercloud_networking_secgroup_rule" "app_to_db" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 5432
  port_range_max    = 5432
  remote_ip_prefix  = var.app_subnet_cidr  # CIDR of app subnet
  security_group_id = var.security_group_id
}

# Optional: Cloud.ru OBS backup configuration
# (If using Cloud.ru native backups to OBS bucket)
# Note: This might require additional provider resources if available


