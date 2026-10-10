terraform {
  required_version = ">= 1.10"

  required_providers {
    upcloud = {
      source  = "UpCloudLtd/upcloud"
      version = "~> 5.46"
    }
  }

  backend "local" {
    path = "terraform.tfstate"
  }
}

provider "upcloud" {
  username = var.upcloud_username
  password = var.upcloud_password
}

locals {
  config = yamldecode(file("${path.module}/../../../config/instances.yaml"))

  instances = var.enabled_instances != null ? [
    for inst in local.config.providers["upcloud"].instances :
    inst if contains(var.enabled_instances, inst.id)
  ] : local.config.providers["upcloud"].instances

  common_labels = {
    managed_by = "terraform"
    project    = "cloud-bench"
    run_id     = var.run_id
    provider   = "upcloud"
  }

  ssh_public_key = file(var.ssh_public_key_path)

  effective_region = var.default_region != "" ? var.default_region : "de-fra1"
}

module "upcloud_instances" {
  source   = "../../modules/upcloud"
  for_each = { for inst in local.instances : inst.id => inst }

  instance_name   = "cloud-bench-upcloud-${each.value.id}-${var.run_id}"
  instance_type   = each.value.id
  zone            = lookup(var.instance_regions, each.value.id, local.effective_region)
  os_image        = var.os_image
  disk_gb         = each.value.disk_gb
  ssh_public_key  = local.ssh_public_key
  allowed_ssh_ips = var.allowed_ssh_ips
  labels          = merge(local.common_labels, { instance_type = each.value.id })
}

locals {
  all_instances = {
    for inst_id, mod in module.upcloud_instances : inst_id => {
      host = mod.server_ip
      name = mod.server_name
    }
  }
}
