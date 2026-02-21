variable "run_id" {
  description = "Unique identifier for this benchmark run"
  type        = string
  default     = "local"

  validation {
    condition     = can(regex("^[a-zA-Z0-9_-]+$", var.run_id))
    error_message = "The run_id must contain only alphanumeric characters, hyphens, and underscores."
  }

  validation {
    condition     = length(var.run_id) >= 1 && length(var.run_id) <= 64
    error_message = "The run_id must be between 1 and 64 characters."
  }
}

variable "cloud_provider" {
  description = "Cloud provider"
  type        = string
  default     = "hetzner"

  validation {
    condition     = can(regex("^(hetzner)$", var.cloud_provider))
    error_message = "Provider must be 'hetzner'."
  }
}

variable "enabled_instances" {
  description = "List of instance IDs to benchmark (null = all from config)"
  type        = list(string)
  default     = null
}

variable "default_region" {
  description = "Default region for instances"
  type        = string
  default     = "fsn1"
}

variable "instance_regions" {
  description = "Map of instance IDs to regions (overrides default)"
  type        = map(string)
  default     = {}
}

variable "ssh_public_key_path" {
  description = "Path to SSH public key"
  type        = string
  default     = "~/.ssh/id_ed25519.pub"
}

variable "allowed_ssh_ips" {
  description = "Allowed IPs for SSH access (CIDR notation). Required for security."
  type        = list(string)

  validation {
    condition     = length(var.allowed_ssh_ips) > 0
    error_message = "At least one IP/CIDR must be specified for SSH access. Use your public IP/32 or a trusted CIDR block."
  }

  validation {
    condition     = alltrue([for ip in var.allowed_ssh_ips : can(regex("^[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}/[0-9]{1,2}$", ip))])
    error_message = "All IPs must be in valid IPv4 CIDR notation (e.g., 1.2.3.4/32)."
  }
}


variable "os_image" {
  description = "OS image for the servers"
  type        = string
  default     = "ubuntu-24.04"

  validation {
    condition     = can(regex("^(ubuntu-[0-9]{2}\\.[0-9]{2}|debian-[0-9]{2}|fedora-[0-9]+)$", var.os_image))
    error_message = "OS image must be a valid Hetzner image format (e.g., ubuntu-24.04, debian-12)."
  }
}

variable "hcloud_token" {
  description = "Hetzner Cloud API token"
  type        = string
  sensitive   = true
}
