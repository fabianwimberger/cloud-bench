variable "instance_name" {
  description = "Name for the GCP compute instance"
  type        = string
}

variable "machine_type" {
  description = "GCP machine type (e.g. e2-medium, n2-standard-2)"
  type        = string
}

variable "instance_arch" {
  description = "Instance architecture: x86_64 or arm64"
  type        = string
  default     = "x86_64"

  validation {
    condition     = contains(["x86_64", "arm64"], var.instance_arch)
    error_message = "instance_arch must be x86_64 or arm64"
  }
}

variable "region" {
  description = "GCP region (e.g. europe-west3)"
  type        = string
}

variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "ssh_public_key" {
  description = "SSH public key content"
  type        = string
}

variable "allowed_ssh_ips" {
  description = "CIDR blocks allowed SSH access"
  type        = list(string)

  validation {
    condition     = length(var.allowed_ssh_ips) > 0
    error_message = "At least one allowed SSH IP must be specified"
  }
}

variable "disk_size_gb" {
  description = "Boot disk size in GB"
  type        = number
  default     = 20
}

variable "disk_type" {
  description = "Boot disk type (pd-balanced, pd-ssd, pd-standard)"
  type        = string
  default     = "pd-balanced"
}

variable "labels" {
  description = "Labels to apply to all resources"
  type        = map(string)
  default     = {}
}
