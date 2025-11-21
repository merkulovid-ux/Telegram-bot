output "vpc_id" {
  description = "ID созданного VPC."
  value       = sbercloud_vpc_v1.this.id
}

output "subnet_ids" {
  description = "ID подсетей по их именам."
  value = {
    for name, subnet in sbercloud_vpc_subnet_v1.subnet :
    name => subnet.id
  }
}

output "security_group_id" {
  description = "ID security group по умолчанию."
  value       = sbercloud_networking_secgroup_v2.default.id
}



