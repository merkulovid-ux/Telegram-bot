variable "vpc_name" {
  description = "Имя создаваемого VPC."
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR блок VPC (например, 10.20.0.0/16)."
  type        = string
}

variable "subnets" {
  description = "Список подсетей для разных зон доступности."
  type = list(object({
    name              = string
    cidr              = string
    gateway_ip        = string
    availability_zone = string
  }))
}

variable "security_group_name" {
  description = "Имя security group по умолчанию."
  type        = string
  default     = "telegram-ai-bot-sg"
}

variable "security_group_description" {
  description = "Описание security group."
  type        = string
  default     = "Default security group for Telegram AI Bot workloads."
}

variable "security_group_rules" {
  description = "Дополнительные ingress правила для security group."
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


