data "openstack_images_image_v2" "os" {
  name_regex  = var.image_name
  most_recent = true
}
