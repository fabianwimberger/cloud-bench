terraform {
  required_version = ">= 1.10"

  required_providers {
    hcloud = {
      source  = "hetznercloud/hcloud"
      version = "~> 1.60"
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
  config = yamldecode(file("${path.module}/../../../config/instances.yaml"))

  instances = var.enabled_instances != null ? [
    for inst in local.config.providers["hetzner"].instances :
    inst if contains(var.enabled_instances, inst.id)
  ] : local.config.providers["hetzner"].instances

  common_labels = {
    managed_by = "terraform"
    project    = "cloud-bench"
    run_id     = var.run_id
    provider   = "hetzner"
  }

  ssh_public_key = file(var.ssh_public_key_path)

  effective_region = var.default_region != "" ? var.default_region : "fsn1"
}

resource "hcloud_ssh_key" "benchmark" {
  name       = "cloud-bench-${var.run_id}"
  public_key = local.ssh_public_key
}

module "hetzner_instances" {
  source   = "../../modules/hetzner"
  for_each = { for inst in local.instances : inst.id => inst }

  instance_name   = "cloud-bench-hetzner-${each.value.id}-${var.run_id}"
  instance_type   = each.value.id
  location        = lookup(var.instance_regions, each.value.id, local.effective_region)
  os_image        = var.os_image
  ssh_key_id      = hcloud_ssh_key.benchmark.id
  ssh_public_key  = local.ssh_public_key
  allowed_ssh_ips = var.allowed_ssh_ips
  labels          = merge(local.common_labels, { instance_type = each.value.id })
}

locals {
  all_instances = {
    for inst_id, mod in module.hetzner_instances : inst_id => {
      host = mod.server_ip
      name = mod.server_name
    }
  }
}
