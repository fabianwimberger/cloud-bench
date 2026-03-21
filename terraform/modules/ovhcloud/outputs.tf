output "server_ip" {
  description = "Public IPv4 address of the instance"
  value       = openstack_compute_instance_v2.benchmark.network[0].fixed_ip_v4
}

output "server_name" {
  description = "Name of the instance"
  value       = openstack_compute_instance_v2.benchmark.name
}

output "instance_id" {
  description = "OpenStack instance ID"
  value       = openstack_compute_instance_v2.benchmark.id
}
