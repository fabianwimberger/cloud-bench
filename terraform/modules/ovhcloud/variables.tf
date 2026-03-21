variable "instance_name" {
  description = "Name for the OVHcloud instance"
  type        = string
}

variable "instance_type" {
  description = "OVHcloud flavor name (e.g. b3-8, c3-4)"
  type        = string
}

variable "region" {
  description = "OVHcloud region (e.g. DE1)"
  type        = string
  default     = "DE1"
}

variable "ssh_key_name" {
  description = "Name for the SSH key resource"
  type        = string
}

variable "ssh_public_key" {
  description = "SSH public key content"
  type        = string
}

variable "labels" {
  description = "Metadata labels applied to the instance"
  type        = map(string)
  default     = {}
}

variable "image_name" {
  description = "OS image name regex to match (e.g. 'Ubuntu 24.04')"
  type        = string
  default     = "Ubuntu 24.04"
}
