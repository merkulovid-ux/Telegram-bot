# Variables for Managed PostgreSQL module

variable "environment" {
  description = "Environment name (dev/stage/prod)"
  type        = string
  default     = "dev"
}

# Network configuration (from network module)
variable "vpc_id" {
  description = "VPC ID where PG cluster will be deployed"
  type        = string
}

variable "subnet_id" {
  description = "Subnet ID for PG cluster (private subnet)"
  type        = string
}

variable "security_group_id" {
  description = "Security Group ID for PG cluster access control"
  type        = string
}

variable "app_subnet_cidr" {
  description = "CIDR of app subnet for security group ingress rules"
  type        = string
}

variable "availability_zone" {
  description = "Availability zone for PG cluster"
  type        = string
  default     = "ru-moscow-1a"
}

# PostgreSQL configuration
variable "pg_version" {
  description = "PostgreSQL version (supported: 12, 13, 14, 15)"
  type        = string
  default     = "15"
  validation {
    condition = contains(["12", "13", "14", "15"], var.pg_version)
    error_message = "PostgreSQL version must be one of: 12, 13, 14, 15"
  }
}

variable "instance_flavor" {
  description = "Instance flavor for PG cluster (e.g., rds.pg.c6.xlarge.4)"
  type        = string
  default     = "rds.pg.c6.large.2"
}

variable "ha_replication_mode" {
  description = "High availability replication mode (async/sync)"
  type        = string
  default     = "async"
}

variable "volume_type" {
  description = "Storage volume type (ULTRAHIGH/HIGH/NORMAL)"
  type        = string
  default     = "ULTRAHIGH"
}

variable "volume_size" {
  description = "Storage volume size in GB"
  type        = number
  default     = 100
  validation {
    condition = var.volume_size >= 100 && var.volume_size <= 4000
    error_message = "Volume size must be between 100 and 4000 GB"
  }
}

variable "max_connections" {
  description = "Maximum number of connections to PostgreSQL"
  type        = number
  default     = 100
}

variable "backup_keep_days" {
  description = "Number of days to keep automated backups"
  type        = number
  default     = 7
  validation {
    condition = var.backup_keep_days >= 1 && var.backup_keep_days <= 732
    error_message = "Backup keep days must be between 1 and 732"
  }
}

# Database configuration
variable "db_admin_user" {
  description = "PostgreSQL admin username"
  type        = string
  default     = "pg_admin"
  validation {
    condition = can(regex("^[a-zA-Z_][a-zA-Z0-9_]*$", var.db_admin_user))
    error_message = "Database username must be valid PostgreSQL identifier"
  }
}
