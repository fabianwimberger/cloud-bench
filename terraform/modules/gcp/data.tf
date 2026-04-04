# Ubuntu 24.04 LTS image lookup - x86_64
data "google_compute_image" "ubuntu_x86" {
  family  = "ubuntu-2404-lts-amd64"
  project = "ubuntu-os-cloud"
}

# Ubuntu 24.04 LTS image lookup - arm64
data "google_compute_image" "ubuntu_arm64" {
  family  = "ubuntu-2404-lts-arm64"
  project = "ubuntu-os-cloud"
}
