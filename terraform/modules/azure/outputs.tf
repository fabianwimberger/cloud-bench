output "server_ip" {
  description = "Public IP address of the instance"
  value       = azurerm_public_ip.benchmark.ip_address
}

output "server_name" {
  description = "Name of the instance"
  value       = var.instance_name
}

output "instance_id" {
  description = "Azure VM resource ID"
  value       = azurerm_linux_virtual_machine.benchmark.id
}

output "resource_group" {
  description = "Resource group containing this instance"
  value       = azurerm_resource_group.benchmark.name
}
