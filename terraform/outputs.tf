output "server_inventory" {
  description = "Computed server attributes including the primary IPv4 addresses"
  value       = local.server_inventory
}

output "ansible_inventory_file" {
  description = "Path of the generated Ansible inventory file"
  value       = local_file.ansible_inventory.filename
}
