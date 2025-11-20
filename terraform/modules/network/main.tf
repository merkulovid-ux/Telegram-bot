terraform {
  required_providers {
    sbercloud = {
      source  = "sbercloud-terraform/sbercloud"
      version = ">= 1.14.0"
    }
  }
}

resource "sbercloud_vpc_v1" "this" {
  name = var.vpc_name
  cidr = var.vpc_cidr
}

resource "sbercloud_vpc_subnet_v1" "subnet" {
  for_each = { for subnet in var.subnets : subnet.name => subnet }

  name              = each.value.name
  cidr              = each.value.cidr
  gateway_ip        = each.value.gateway_ip
  vpc_id            = sbercloud_vpc_v1.this.id
  availability_zone = each.value.availability_zone
}

resource "sbercloud_networking_secgroup_v2" "default" {
  name        = var.security_group_name
  description = var.security_group_description
}

resource "sbercloud_networking_secgroup_rule_v2" "egress_all" {
  direction         = "egress"
  ethertype         = "IPv4"
  remote_ip_prefix  = "0.0.0.0/0"
  security_group_id = sbercloud_networking_secgroup_v2.default.id
  description       = "Allow all outbound traffic"
}

resource "sbercloud_networking_secgroup_rule_v2" "ingress" {
  for_each = {
    for rule in var.security_group_rules :
    "${rule.protocol}-${rule.port_range_min}-${rule.port_range_max}-${rule.description}" => rule
  }

  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = each.value.protocol
  port_range_min    = each.value.port_range_min
  port_range_max    = each.value.port_range_max
  remote_ip_prefix  = each.value.remote_ip_prefix
  security_group_id = sbercloud_networking_secgroup_v2.default.id
  description       = each.value.description
}

