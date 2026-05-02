terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 7.1"
    }
  }
}

locals {
  image = var.instance_arch == "arm64" ? data.google_compute_image.ubuntu_arm64.self_link : data.google_compute_image.ubuntu_x86.self_link

  cloud_init = templatefile("${path.module}/cloud-init.yml.tmpl", {})

  zone = var.zone != "" ? var.zone : "${var.region}-${var.zone_suffix}"

  # 4th-gen+ families (C4, C4A, C4D, N4, N4A) require hyperdisk; older families use pd-* disks
  needs_hyperdisk     = can(regex("^(c4|c4a|c4d|n4|n4a)-", var.machine_type))
  effective_disk_type = local.needs_hyperdisk ? "hyperdisk-balanced" : var.disk_type
}

# --- Networking ---

resource "google_compute_firewall" "benchmark_ssh" {
  name    = "${var.instance_name}-allow-ssh"
  network = "default"
  project = var.project_id

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  allow {
    protocol = "icmp"
  }

  source_ranges = var.allowed_ssh_ips
  target_tags   = ["cloud-bench-${var.labels["run_id"]}"]
}

# --- Compute Instance ---

resource "google_compute_instance" "benchmark" {
  name         = var.instance_name
  machine_type = var.machine_type
  zone         = local.zone
  project      = var.project_id

  tags = ["cloud-bench-${var.labels["run_id"]}"]

  labels = var.labels

  boot_disk {
    initialize_params {
      image = local.image
      size  = var.disk_size_gb
      type  = local.effective_disk_type
    }
  }

  network_interface {
    network = "default"

    access_config {
      # Ephemeral public IP
    }
  }

  metadata = {
    ssh-keys  = "ubuntu:${var.ssh_public_key}"
    user-data = local.cloud_init
  }

  scheduling {
    automatic_restart   = false
    on_host_maintenance = "MIGRATE"
    preemptible         = false
  }
}
