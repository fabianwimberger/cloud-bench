variable "instance_name" {
  description = "Name tag for the EC2 instance"
  type        = string
}

variable "instance_type" {
  description = "AWS EC2 instance type (e.g. t3.medium)"
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

variable "ssh_key_name" {
  description = "Name for the AWS key pair"
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

variable "ebs_volume_size" {
  description = "EBS root volume size in GB"
  type        = number
  default     = 20
}

variable "ebs_volume_type" {
  description = "EBS volume type"
  type        = string
  default     = "gp3"
}

variable "labels" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}

variable "enable_unlimited_credits" {
  description = "Enable unlimited CPU credits for T-series burstable instances"
  type        = bool
  default     = true
}
