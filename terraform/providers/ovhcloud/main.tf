terraform {
  required_version = ">= 1.10"

  required_providers {
    openstack = {
      source  = "terraform-provider-openstack/openstack"
      version = "~> 3.0"
    }
  }

  backend "local" {
    path = "terraform.tfstate"
  }
}

provider "openstack" {
  auth_url         = "https://auth.cloud.ovh.net/v3"
  user_name        = var.ovh_openstack_username
  password         = var.ovh_openstack_password
  tenant_id        = var.ovh_cloud_project_id
  user_domain_name = "Default"
  region           = local.effective_region
}

locals {
  config = yamldecode(file("${path.module}/../../../config/instances.yaml"))

  instances = var.enabled_instances != null ? [
    for inst in local.config.providers["ovhcloud"].instances :
    inst if contains(var.enabled_instances, inst.id)
  ] : local.config.providers["ovhcloud"].instances

  common_labels = {
    managed_by = "terraform"
    project    = "cloud-bench"
    run_id     = var.run_id
    provider   = "ovhcloud"
  }

  ssh_public_key = file(var.ssh_public_key_path)

  effective_region = var.default_region != "" ? var.default_region : "DE1"
}

module "ovhcloud_instances" {
  source   = "../../modules/ovhcloud"
  for_each = { for inst in local.instances : inst.id => inst }

  instance_name  = "cloud-bench-ovhcloud-${each.value.id}-${var.run_id}"
  instance_type  = each.value.id
  ssh_key_name   = "cloud-bench-${each.value.id}-${var.run_id}"
  ssh_public_key = local.ssh_public_key
  labels         = merge(local.common_labels, { instance_type = each.value.id })
}

locals {
  all_instances = {
    for inst_id, mod in module.ovhcloud_instances : inst_id => {
      host = mod.server_ip
      name = mod.server_name
    }
  }
}
