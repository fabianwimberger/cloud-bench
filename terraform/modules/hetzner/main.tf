terraform {
  required_providers {
    hcloud = {
      source  = "hetznercloud/hcloud"
      version = "~> 1.50"
    }
  }
}

locals {
  cloud_init = templatefile("${path.module}/cloud-init.yml.tmpl", {
    ssh_public_key = var.ssh_public_key
  })
}

resource "hcloud_server" "benchmark" {
  name        = var.instance_name
  server_type = var.instance_type
  image       = var.os_image
  location    = var.location
  ssh_keys    = [var.ssh_key_id]
  user_data   = local.cloud_init

  labels = merge(var.labels, {
    managed_by = "terraform"
    project    = "cloud-bench"
  })
}

resource "hcloud_firewall" "benchmark" {
  count = var.enable_firewall ? 1 : 0
  name  = "${var.instance_name}-firewall"

  rule {
    direction  = "in"
    protocol   = "tcp"
    port       = "22"
    source_ips = ["0.0.0.0/0", "::/0"]
  }

  rule {
    direction  = "in"
    protocol   = "icmp"
    source_ips = ["0.0.0.0/0", "::/0"]
  }
}

resource "hcloud_firewall_attachment" "benchmark" {
  count       = var.enable_firewall ? 1 : 0
  firewall_id = hcloud_firewall.benchmark[0].id
  server_ids  = [hcloud_server.benchmark.id]
}
