output "server_ip" {
  description = "Public IP address of the instance"
  value       = oci_core_instance.benchmark.public_ip
}

output "server_name" {
  description = "Name of the instance"
  value       = var.instance_name
}

output "instance_id" {
  description = "OCI instance OCID"
  value       = oci_core_instance.benchmark.id
}
