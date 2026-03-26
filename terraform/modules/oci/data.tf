# Look up the latest Ubuntu 24.04 image for the target architecture
data "oci_core_images" "ubuntu" {
  compartment_id           = var.compartment_id
  operating_system         = "Canonical Ubuntu"
  operating_system_version = "24.04"
  shape                    = var.instance_shape
  sort_by                  = "TIMECREATED"
  sort_order               = "DESC"

  filter {
    name   = "display_name"
    values = [var.image_name]
    regex  = true
  }
}

# Availability domains in the region
data "oci_identity_availability_domains" "ads" {
  compartment_id = var.compartment_id
}
