terraform {
  required_providers {
    ovh = {
      source  = "ovh/ovh"
      version = "~> 2.12"
    }
  }
}

locals {
  cloud_init = templatefile("${path.module}/cloud-init.yml.tmpl", {
    ssh_public_key = var.ssh_public_key
  })
}

resource "ovh_cloud_project_ssh_key" "benchmark" {
  service_name = var.service_name
  name         = var.ssh_key_name
  public_key   = var.ssh_public_key
}

resource "ovh_cloud_project_instance" "benchmark" {
  service_name   = var.service_name
  name           = var.instance_name
  region         = var.region
  billing_period = "hourly"

  flavor {
    flavor_id = local.flavor.id
  }

  boot_from {
    image_id = local.image.id
  }

  network {
    public = true
  }

  ssh_key {
    name = ovh_cloud_project_ssh_key.benchmark.name
  }

  user_data = local.cloud_init
}
