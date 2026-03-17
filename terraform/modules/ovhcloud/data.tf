data "ovh_cloud_project_flavors" "this" {
  service_name = var.service_name
  region       = var.region
}

data "ovh_cloud_project_images" "this" {
  service_name = var.service_name
  region       = var.region
}

locals {
  # Find the flavor matching our instance type name
  flavor = [
    for f in data.ovh_cloud_project_flavors.this.flavors :
    f if f.name == var.instance_type
  ][0]

  # Find the Ubuntu 24.04 image
  image = [
    for img in data.ovh_cloud_project_images.this.images :
    img if can(regex("Ubuntu 24\\.04", img.name)) && img.status == "active"
  ][0]
}
