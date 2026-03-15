terraform {
  required_version = ">= 1.10"

  required_providers {
    hcloud = {
      source  = "hetznercloud/hcloud"
      version = "~> 1.50"
    }
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "local" {
    path = "terraform.tfstate"
  }
}

provider "hcloud" {
  token = var.hcloud_token
}

provider "aws" {
  region     = var.cloud_provider == "aws" ? local.effective_region : "us-east-1"
  access_key = var.aws_access_key_id
  secret_key = var.aws_secret_access_key

  # Skip validation when not using AWS to avoid credential errors
  skip_credentials_validation = var.cloud_provider != "aws"
  skip_requesting_account_id  = var.cloud_provider != "aws"
  skip_metadata_api_check     = var.cloud_provider != "aws"
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

  # Auto-detect region based on provider if not explicitly set
  effective_region = var.default_region != "" ? var.default_region : lookup(
    {
      hetzner = "fsn1"
      aws     = "eu-central-1"
    },
    var.cloud_provider,
    "fsn1"
  )

  # Map arch from config format to AWS format
  arch_map = {
    "X86"   = "x86_64"
    "ARM64" = "arm64"
  }
}

resource "hcloud_ssh_key" "benchmark" {
  count      = var.cloud_provider == "hetzner" ? 1 : 0
  name       = "cloud-bench-${var.run_id}"
  public_key = local.ssh_public_key
}

module "hetzner_instances" {
  source   = "./modules/hetzner"
  for_each = var.cloud_provider == "hetzner" ? { for inst in local.instances : inst.id => inst } : {}

  instance_name   = "cloud-bench-${var.cloud_provider}-${each.value.id}-${var.run_id}"
  instance_type   = each.value.id
  location        = lookup(var.instance_regions, each.value.id, local.effective_region)
  os_image        = var.os_image
  ssh_key_id      = hcloud_ssh_key.benchmark[0].id
  ssh_public_key  = local.ssh_public_key
  allowed_ssh_ips = var.allowed_ssh_ips
  labels          = merge(local.common_labels, { instance_type = each.value.id })
}

module "aws_instances" {
  source   = "./modules/aws"
  for_each = var.cloud_provider == "aws" ? { for inst in local.instances : inst.id => inst } : {}

  instance_name            = "cloud-bench-${var.cloud_provider}-${replace(each.value.id, ".", "-")}-${var.run_id}"
  instance_type            = each.value.id
  instance_arch            = lookup(local.arch_map, each.value.arch, "x86_64")
  ssh_key_name             = "cloud-bench-${replace(each.value.id, ".", "-")}-${var.run_id}"
  ssh_public_key           = local.ssh_public_key
  allowed_ssh_ips          = var.allowed_ssh_ips
  ebs_volume_size          = var.aws_ebs_size
  labels                   = merge(local.common_labels, { instance_type = each.value.id })
  enable_unlimited_credits = true
}

locals {
  all_instances = var.cloud_provider == "hetzner" ? {
    for inst_id, mod in module.hetzner_instances : inst_id => {
      host = mod.server_ip
      name = mod.server_name
    }
    } : {
    for inst_id, mod in module.aws_instances : inst_id => {
      host = mod.server_ip
      name = mod.server_name
    }
  }
}
