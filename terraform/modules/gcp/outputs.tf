output "server_ip" {
  description = "Public IP address of the instance"
  value       = google_compute_instance.benchmark.network_interface[0].access_config[0].nat_ip
}

output "server_name" {
  description = "Name of the instance"
  value       = var.instance_name
}

output "instance_id" {
  description = "GCP instance ID"
  value       = google_compute_instance.benchmark.instance_id
}

output "zone" {
  description = "GCP zone where the instance is deployed"
  value       = google_compute_instance.benchmark.zone
}
