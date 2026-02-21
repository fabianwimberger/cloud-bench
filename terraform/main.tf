terraform {
  required_version = ">= 1.10"

  required_providers {
    hcloud = {
      source  = "hetznercloud/hcloud"
      version = "~> 1.50"
    }
  }

  backend "local" {
    path = "terraform.tfstate"
  }
}

provider "hcloud" {
  token = var.hcloud_token
}

locals {
  config = yamldecode(file("${path.module}/../config/instances.yaml"))

  instances = var.enabled_instances != null ? [
    for inst in local.config.providers[var.cloud_provider].instances :
    inst if contains(var.enabled_instances, inst.id)
  ] : local.config.providers[var.cloud_provider].instances

  common_labels = {
    managed_by = "terraform"
    project    = "cloud-bench"
    run_id     = var.run_id
    provider   = var.cloud_provider
  }

  ssh_public_key = file(var.ssh_public_key_path)

  effective_region = var.default_region
}

resource "hcloud_ssh_key" "benchmark" {
  name       = "cloud-bench-${var.run_id}"
  public_key = local.ssh_public_key
}

module "hetzner_instances" {
  source   = "./modules/hetzner"
  for_each = { for inst in local.instances : inst.id => inst }

  instance_name   = "cloud-bench-${var.cloud_provider}-${each.value.id}-${var.run_id}"
  instance_type   = each.value.id
  location        = lookup(var.instance_regions, each.value.id, local.effective_region)
  os_image        = var.os_image
  ssh_key_id      = hcloud_ssh_key.benchmark.id
  ssh_public_key  = local.ssh_public_key
  allowed_ssh_ips = var.allowed_ssh_ips
  labels          = merge(local.common_labels, { instance_type = each.value.id })
}

# Outputs defined in outputs.tf
