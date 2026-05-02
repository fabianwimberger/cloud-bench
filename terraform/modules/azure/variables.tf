variable "instance_name" {
  description = "Name for the Azure VM and associated resources"
  type        = string
}

variable "instance_type" {
  description = "Azure VM size (e.g. Standard_D2s_v5)"
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
  description = "Azure region (e.g. westeurope)"
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
  description = "OS disk size in GB"
  type        = number
  default     = 30
}

variable "disk_type" {
  description = "OS disk storage account type (Premium_LRS, Standard_LRS, StandardSSD_LRS)"
  type        = string
  default     = "Premium_LRS"

  validation {
    condition     = contains(["Premium_LRS", "Standard_LRS", "StandardSSD_LRS", "UltraSSD_LRS", "Premium_ZRS", "StandardSSD_ZRS"], var.disk_type)
    error_message = "disk_type must be a valid Azure managed disk storage type"
  }
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}
