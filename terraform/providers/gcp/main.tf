terraform {
  required_version = ">= 1.10"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 7.1"
    }
  }

  backend "local" {
    path = "terraform.tfstate"
  }
}

provider "google" {
  project     = var.gcp_project_id
  region      = local.effective_region
  credentials = var.gcp_credentials
}

locals {
  config = yamldecode(file("${path.module}/../../../config/instances.yaml"))

  instances = var.enabled_instances != null ? [
    for inst in local.config.providers["gcp"].instances :
    inst if contains(var.enabled_instances, inst.id)
  ] : local.config.providers["gcp"].instances

  common_labels = {
    managed_by = "terraform"
    project    = "cloud-bench"
    run_id     = var.run_id
    provider   = "gcp"
  }

  ssh_public_key = file(var.ssh_public_key_path)

  effective_region = var.default_region != "" ? var.default_region : "europe-west3"

  arch_map = {
    "X86"   = "x86_64"
    "ARM64" = "arm64"
  }
}

module "gcp_instances" {
  source   = "../../modules/gcp"
  for_each = { for inst in local.instances : inst.id => inst }

  instance_name   = "cloud-bench-gcp-${each.value.id}-${var.run_id}"
  machine_type    = each.value.id
  instance_arch   = lookup(local.arch_map, each.value.arch, "x86_64")
  region          = lookup(var.instance_regions, each.value.id, local.effective_region)
  project_id      = var.gcp_project_id
  ssh_public_key  = local.ssh_public_key
  allowed_ssh_ips = var.allowed_ssh_ips
  disk_size_gb    = var.gcp_disk_size
  labels          = merge(local.common_labels, { instance_type = replace(each.value.id, ".", "-") })
}

locals {
  all_instances = {
    for inst_id, mod in module.gcp_instances : inst_id => {
      host = mod.server_ip
      name = mod.server_name
    }
  }
}
