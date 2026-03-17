output "server_ip" {
  description = "Public IPv4 address of the instance"
  value = [
    for addr in ovh_cloud_project_instance.benchmark.addresses :
    addr.ip if addr.version == 4
  ][0]
}

output "server_name" {
  description = "Name of the instance"
  value       = var.instance_name
}

output "instance_id" {
  description = "OVHcloud instance ID"
  value       = ovh_cloud_project_instance.benchmark.id
}
