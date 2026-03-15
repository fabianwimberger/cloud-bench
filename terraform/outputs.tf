output "ansible_inventory" {
  description = "Ansible inventory file content"
  value = templatefile("${path.module}/inventory.tmpl", {
    instances = local.all_instances
    provider  = var.cloud_provider
    region    = local.effective_region
  })
}

output "server_ips" {
  description = "Server IP addresses"
  value = {
    for inst_id, inst in local.all_instances : inst_id => inst.host
  }
}

output "server_names" {
  description = "Server names"
  value = {
    for inst_id, inst in local.all_instances : inst_id => inst.name
  }
}

output "instances_created" {
  description = "List of instance IDs that were created"
  value       = keys(local.all_instances)
}
