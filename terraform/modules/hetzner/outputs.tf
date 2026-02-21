output "instance_id" {
  description = "ID of the created server"
  value       = hcloud_server.benchmark.id
}

output "public_ip" {
  description = "Public IPv4 address"
  value       = hcloud_server.benchmark.ipv4_address
}

output "server_ip" {
  description = "Server public IP address (alias for compatibility)"
  value       = hcloud_server.benchmark.ipv4_address
}

output "server_name" {
  description = "Server name"
  value       = hcloud_server.benchmark.name
}

output "instance_type" {
  description = "Server type"
  value       = hcloud_server.benchmark.server_type
}

output "location" {
  description = "Datacenter location"
  value       = hcloud_server.benchmark.location
}

output "ssh_connection_string" {
  description = "SSH connection string"
  value       = "root@${hcloud_server.benchmark.ipv4_address}"
}
