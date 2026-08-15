terraform {
  required_version = ">= 1.10"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }

  backend "local" {
    path = "terraform.tfstate"
  }
}

provider "azurerm" {
  features {}
  subscription_id = var.azure_subscription_id
  client_id       = var.azure_client_id
  client_secret   = var.azure_client_secret
  tenant_id       = var.azure_tenant_id
  use_cli         = false
  use_msi         = false
  use_oidc        = false
}

locals {
  config = yamldecode(file("${path.module}/../../../config/instances.yaml"))

  instances = var.enabled_instances != null ? [
    for inst in local.config.providers["azure"].instances :
    inst if contains(var.enabled_instances, inst.id)
  ] : local.config.providers["azure"].instances

  common_labels = {
    managed_by = "terraform"
    project    = "cloud-bench"
    run_id     = var.run_id
    provider   = "azure"
  }

  ssh_public_key = file(var.ssh_public_key_path)

  effective_region = var.default_region != "" ? var.default_region : "northeurope"

  arch_map = {
    "X86"   = "x86_64"
    "ARM64" = "arm64"
  }
}

module "azure_instances" {
  source   = "../../modules/azure"
  for_each = { for inst in local.instances : inst.id => inst }

  instance_name   = "cloud-bench-azure-${replace(each.value.id, "_", "-")}-${var.run_id}"
  instance_type   = each.value.id
  instance_arch   = lookup(local.arch_map, each.value.arch, "x86_64")
  region          = lookup(var.instance_regions, each.value.id, local.effective_region)
  ssh_public_key  = local.ssh_public_key
  allowed_ssh_ips = var.allowed_ssh_ips
  disk_size_gb    = var.azure_disk_size
  tags            = merge(local.common_labels, { instance_type = replace(each.value.id, "_", "-") })
}

locals {
  all_instances = {
    for inst_id, mod in module.azure_instances : inst_id => {
      host = mod.server_ip
      name = mod.server_name
    }
  }
}
