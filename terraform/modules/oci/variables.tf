variable "instance_name" {
  description = "Name for the OCI compute instance"
  type        = string
}

variable "instance_shape" {
  description = "OCI compute shape (e.g. VM.Standard.E4.Flex)"
  type        = string
}

variable "instance_ocpus" {
  description = "Number of OCPUs for flex shapes"
  type        = number
  default     = 1
}

variable "instance_memory_gb" {
  description = "Memory in GB for flex shapes"
  type        = number
  default     = 8
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

variable "compartment_id" {
  description = "OCI compartment OCID for resource creation"
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

variable "boot_volume_size_gb" {
  description = "Boot volume size in GB"
  type        = number
  default     = 50
}

variable "labels" {
  description = "Freeform tags to apply to all resources"
  type        = map(string)
  default     = {}
}

variable "image_name" {
  description = "OS image display name pattern to match (regex). Leave empty for auto-detection based on architecture."
  type        = string
  default     = ""
}
