terraform {
  required_providers {
    openstack = {
      source  = "terraform-provider-openstack/openstack"
      version = "~> 3.0"
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
  user_data = templatefile("${path.module}/cloud-init.yml.tmpl", {
    ssh_public_key = var.ssh_public_key
  })

  network {
    name = "Ext-Net"
  }

  metadata = var.labels
}
