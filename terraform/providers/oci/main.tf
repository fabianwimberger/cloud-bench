terraform {
  required_version = ">= 1.10"

  required_providers {
    oci = {
      source  = "oracle/oci"
      version = "~> 6.0"
    }
  }

  backend "local" {
    path = "terraform.tfstate"
  }
}

provider "oci" {
  tenancy_ocid = var.oci_tenancy_ocid
  user_ocid    = var.oci_user_ocid
  fingerprint  = var.oci_fingerprint
  private_key  = var.oci_private_key
  region       = local.effective_region
}

locals {
  config = yamldecode(file("${path.module}/../../../config/instances.yaml"))

  instances = var.enabled_instances != null ? [
    for inst in local.config.providers["oci"].instances :
    inst if contains(var.enabled_instances, inst.id)
  ] : local.config.providers["oci"].instances

  common_labels = {
    managed_by = "terraform"
    project    = "cloud-bench"
    run_id     = var.run_id
    provider   = "oci"
  }

  ssh_public_key = file(var.ssh_public_key_path)

  effective_region = var.default_region != "" ? var.default_region : "eu-frankfurt-1"

  arch_map = {
    "X86"   = "x86_64"
    "ARM64" = "arm64"
  }
}

module "oci_instances" {
  source   = "../../modules/oci"
  for_each = { for inst in local.instances : inst.id => inst }

  instance_name      = "cloud-bench-oci-${each.value.id}-${var.run_id}"
  instance_shape     = each.value.shape
  instance_ocpus     = each.value.ocpus
  instance_memory_gb = each.value.ram_gb
  instance_arch      = lookup(local.arch_map, each.value.arch, "x86_64")
  compartment_id     = var.oci_compartment_id
  ssh_public_key     = local.ssh_public_key
  allowed_ssh_ips    = var.allowed_ssh_ips
  labels             = merge(local.common_labels, { instance_type = each.value.id })
}

locals {
  all_instances = {
    for inst_id, mod in module.oci_instances : inst_id => {
      host = mod.server_ip
      name = mod.server_name
    }
  }
}
