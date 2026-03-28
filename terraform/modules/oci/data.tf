# Look up the latest Ubuntu 24.04 image for the target architecture
# ARM images include "aarch64" in the name, x86 images do not
locals {
  image_name_pattern = var.image_name != "" ? var.image_name : (
    var.instance_arch == "arm64" ? "Canonical-Ubuntu-24.04-aarch64-2" : "Canonical-Ubuntu-24.04-2"
  )
}

data "oci_core_images" "ubuntu" {
  compartment_id           = var.compartment_id
  operating_system         = "Canonical Ubuntu"
  operating_system_version = "24.04"
  shape                    = var.instance_shape
  sort_by                  = "TIMECREATED"
  sort_order               = "DESC"

  filter {
    name   = "display_name"
    values = [local.image_name_pattern]
    regex  = true
  }
}

# Availability domains in the region
data "oci_identity_availability_domains" "ads" {
  compartment_id = var.compartment_id
}
