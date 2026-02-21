output "ansible_inventory" {
  description = "Ansible inventory file content"
  value = templatefile("${path.module}/inventory.tmpl", {
    instances = {
      for inst_id, module in module.hetzner_instances : inst_id => {
        host = module.server_ip
        name = module.server_name
      }
    }
    provider = var.cloud_provider
    region   = local.effective_region
  })
}

output "server_ips" {
  description = "Server IP addresses"
  value = {
    for inst_id, module in module.hetzner_instances : inst_id => module.server_ip
  }
}

output "server_names" {
  description = "Server names"
  value = {
    for inst_id, module in module.hetzner_instances : inst_id => module.server_name
  }
}

output "instances_created" {
  description = "List of instance IDs that were created"
  value       = keys(module.hetzner_instances)
}
