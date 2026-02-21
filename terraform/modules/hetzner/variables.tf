variable "instance_name" {
  description = "Name of the benchmark instance"
  type        = string
}

variable "instance_type" {
  description = "Hetzner server type"
  type        = string
  default     = "cx23"
}

variable "location" {
  description = "Hetzner datacenter location"
  type        = string
  default     = "fsn1"
}

variable "os_image" {
  description = "OS image for the server"
  type        = string
  default     = "ubuntu-24.04"
}

variable "ssh_key_id" {
  description = "ID of the Hetzner SSH key resource"
  type        = number
}

variable "ssh_public_key" {
  description = "SSH public key for instance access (used in cloud-init)"
  type        = string
}

variable "labels" {
  description = "Additional labels for the instance"
  type        = map(string)
  default     = {}
}

variable "enable_firewall" {
  description = "Enable Hetzner Cloud Firewall"
  type        = bool
  default     = true
}

variable "allowed_ssh_ips" {
  description = "Allowed IPs for SSH access (use CIDR notation). Must be explicitly set."
  type        = list(string)
  default     = []

  validation {
    condition     = length(var.allowed_ssh_ips) > 0
    error_message = "At least one IP/CIDR must be specified for SSH access."
  }
}
