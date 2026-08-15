terraform {
  required_version = ">= 1.10"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }

  backend "local" {
    path = "terraform.tfstate"
  }
}

provider "aws" {
  region     = local.effective_region
  access_key = var.aws_access_key_id
  secret_key = var.aws_secret_access_key
}

locals {
  config = yamldecode(file("${path.module}/../../../config/instances.yaml"))

  instances = var.enabled_instances != null ? [
    for inst in local.config.providers["aws"].instances :
    inst if contains(var.enabled_instances, inst.id)
  ] : local.config.providers["aws"].instances

  common_labels = {
    managed_by = "terraform"
    project    = "cloud-bench"
    run_id     = var.run_id
    provider   = "aws"
  }

  ssh_public_key = file(var.ssh_public_key_path)

  effective_region = var.default_region != "" ? var.default_region : "eu-central-1"

  arch_map = {
    "X86"   = "x86_64"
    "ARM64" = "arm64"
  }
}

module "aws_instances" {
  source   = "../../modules/aws"
  for_each = { for inst in local.instances : inst.id => inst }

  instance_name            = "cloud-bench-aws-${replace(each.value.id, ".", "-")}-${var.run_id}"
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
  all_instances = {
    for inst_id, mod in module.aws_instances : inst_id => {
      host = mod.server_ip
      name = mod.server_name
    }
  }
}
