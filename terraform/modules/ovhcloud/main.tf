terraform {
  required_providers {
    openstack = {
      source  = "terraform-provider-openstack/openstack"
      version = "~> 2.0"
    }
  }
}

resource "openstack_compute_keypair_v2" "benchmark" {
  name       = var.ssh_key_name
  public_key = var.ssh_public_key
}

resource "openstack_compute_instance_v2" "benchmark" {
  name        = var.instance_name
  flavor_name = var.instance_type
  image_id    = data.openstack_images_image_v2.os.id
  key_pair    = openstack_compute_keypair_v2.benchmark.name
  user_data   = file("${path.module}/cloud-init.yml.tmpl")

  network {
    name = "Ext-Net"
  }

  metadata = var.labels
}
