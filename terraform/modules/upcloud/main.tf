terraform {
  required_providers {
    upcloud = {
      source  = "UpCloudLtd/upcloud"
      version = "~> 5.46"
    }
  }
}

locals {
  # Hostnames allow letters, digits and hyphens only; plan names carry
  # upper case, and run IDs may carry underscores.
  hostname = lower(replace(var.instance_name, "_", "-"))

  # The plan price covers its own storage tier only: Standard for Starter,
  # MaxIOPS for everything else. Any other tier is billed on top.
  storage_tier = startswith(var.instance_type, "STARTER-") ? "standard" : "maxiops"
}

resource "upcloud_server" "benchmark" {
  hostname = local.hostname
  title    = var.instance_name
  zone     = var.zone
  plan     = var.instance_type

  # Required for cloud-init based templates to receive user_data.
  metadata = true

  # With the firewall on, anything not matched by a rule below is dropped.
  # Trial accounts refuse a server without it.
  firewall = true

  user_data = templatefile("${path.module}/cloud-init.yml.tmpl", {
    ssh_public_key = var.ssh_public_key
  })

  template {
    storage = var.os_image
    size    = var.disk_gb
    tier    = local.storage_tier
  }

  network_interface {
    type              = "public"
    ip_address_family = "IPv4"
  }

  login {
    user            = "root"
    keys            = [var.ssh_public_key]
    create_password = false
  }

  labels = var.labels
}

resource "upcloud_firewall_rules" "benchmark" {
  server_id = upcloud_server.benchmark.id

  # Provisioning, benchmark and cleanup run as separate jobs from different
  # runner addresses, so SSH is not tied to one of them. Login is key-only.
  firewall_rule {
    action                 = "accept"
    comment                = "SSH"
    direction              = "in"
    family                 = "IPv4"
    protocol               = "tcp"
    destination_port_start = "22"
    destination_port_end   = "22"
  }

  # Replies to outbound connections are let back in, so package installs
  # and DNS need no inbound rule of their own.
  firewall_rule {
    action    = "accept"
    comment   = "All outbound"
    direction = "out"
  }
}
