output "server_ip" {
  description = "Public IPv4 address of the server"
  value       = upcloud_server.benchmark.network_interface[0].ip_address
}

output "server_name" {
  description = "Name of the server"
  value       = upcloud_server.benchmark.title
}

output "instance_id" {
  description = "UpCloud server UUID"
  value       = upcloud_server.benchmark.id
}
