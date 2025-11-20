# Outputs for Managed PostgreSQL module

output "cluster_id" {
  description = "ID of the created PostgreSQL cluster"
  value       = sbercloud_rds_instance_v3.main.id
}

output "cluster_name" {
  description = "Name of the created PostgreSQL cluster"
  value       = sbercloud_rds_instance_v3.main.name
}

output "db_endpoint" {
  description = "Internal/private endpoint for PostgreSQL cluster"
  value       = sbercloud_rds_instance_v3.main.private_ips[0]
  sensitive   = false  # Public IP if needed, but prefer private
}

output "db_port" {
  description = "PostgreSQL port (default 5432)"
  value       = 5432
}

output "db_name" {
  description = "Name of the created database"
  value       = sbercloud_rds_database.main.name
}

output "db_admin_user" {
  description = "PostgreSQL admin username"
  value       = var.db_admin_user
}

# Password should be retrieved from Vault separately
# Do NOT output passwords directly in Terraform!
output "vault_secret_path" {
  description = "Path to database credentials in Vault (format: /v1/secret/data/pg_credentials)"
  value       = "/v1/secret/data/pg_credentials"
}

# Connection string template (without sensitive data)
output "db_connection_template" {
  description = "Database connection string template (replace PASSWORD with value from Vault)"
  value       = "postgresql://${var.db_admin_user}:PASSWORD@${sbercloud_rds_instance_v3.main.private_ips[0]}:${local.db_port}/${local.db_name}"
  sensitive   = false
}
