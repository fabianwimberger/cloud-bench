variable "instance_name" {
  description = "Name for the UpCloud server"
  type        = string
}

variable "instance_type" {
  description = "UpCloud plan name (e.g. STARTER-2xCPU-4GB, PREMIUM-4xCPU-8GB)"
  type        = string
}

variable "zone" {
  description = "UpCloud zone (e.g. de-fra1)"
  type        = string
  default     = "de-fra1"
}

variable "os_image" {
  description = "OS template title"
  type        = string
  default     = "Ubuntu Server 24.04 LTS (Noble Numbat)"
}

variable "disk_gb" {
  description = "Size of the OS disk in GB (the storage included in the plan)"
  type        = number
}

variable "ssh_public_key" {
  description = "SSH public key content"
  type        = string
}

variable "labels" {
  description = "Labels applied to the server"
  type        = map(string)
  default     = {}
}

variable "allowed_ssh_ips" {
  description = "Allowed IPs for SSH access (CIDR notation)"
  type        = list(string)
}
