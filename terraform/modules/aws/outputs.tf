output "server_ip" {
  description = "Public IP address of the instance"
  value       = aws_instance.benchmark.public_ip
}

output "server_name" {
  description = "Name of the instance"
  value       = var.instance_name
}

output "instance_id" {
  description = "AWS instance ID"
  value       = aws_instance.benchmark.id
}
