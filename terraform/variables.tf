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
    condition     = can(regex("^(hetzner|aws)$", var.cloud_provider))
    error_message = "Provider must be 'hetzner' or 'aws'."
  }
}

variable "enabled_instances" {
  description = "List of instance IDs to benchmark (null = all from config)"
  type        = list(string)
  default     = null
}

variable "default_region" {
  description = "Default region for instances (empty = auto-detect based on provider)"
  type        = string
  default     = ""
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
  description = "OS image for the servers (Hetzner format or AWS AMI ID)"
  type        = string
  default     = "ubuntu-24.04"

  validation {
    condition     = can(regex("^(ubuntu-[0-9]{2}\\.[0-9]{2}|debian-[0-9]{2}|fedora-[0-9]+|ami-[a-z0-9]+)$", var.os_image))
    error_message = "OS image must be a valid Hetzner image (e.g., ubuntu-24.04) or AWS AMI ID (e.g., ami-12345678)."
  }
}

variable "hcloud_token" {
  description = "Hetzner Cloud API token"
  type        = string
  sensitive   = true
}

variable "aws_access_key_id" {
  description = "AWS access key ID"
  type        = string
  sensitive   = true
  default     = ""
}

variable "aws_secret_access_key" {
  description = "AWS secret access key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "aws_ebs_size" {
  description = "EBS volume size in GB for AWS instances"
  type        = number
  default     = 20
}
