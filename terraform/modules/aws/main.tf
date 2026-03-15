terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

locals {
  ami_id = var.instance_arch == "arm64" ? data.aws_ami.ubuntu_arm64.id : data.aws_ami.ubuntu_x86.id

  cloud_init = templatefile("${path.module}/cloud-init.yml.tmpl", {
    ssh_public_key = var.ssh_public_key
  })

  # T-series instances support burstable credit specification
  is_burstable = can(regex("^t[234]", var.instance_type))
}

resource "aws_key_pair" "benchmark" {
  key_name   = var.ssh_key_name
  public_key = var.ssh_public_key

  tags = var.labels
}

resource "aws_security_group" "benchmark" {
  name_prefix = "${var.instance_name}-"
  description = "Cloud-bench benchmark instance security group"
  vpc_id      = data.aws_vpc.default.id

  # SSH access from allowed IPs
  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.allowed_ssh_ips
  }

  # ICMP (ping) from allowed IPs
  ingress {
    description = "ICMP"
    from_port   = -1
    to_port     = -1
    protocol    = "icmp"
    cidr_blocks = var.allowed_ssh_ips
  }

  # Allow all outbound
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.labels, {
    Name = "${var.instance_name}-sg"
  })
}

resource "aws_instance" "benchmark" {
  ami                         = local.ami_id
  instance_type               = var.instance_type
  key_name                    = aws_key_pair.benchmark.key_name
  vpc_security_group_ids      = [aws_security_group.benchmark.id]
  subnet_id                   = data.aws_subnets.default.ids[0]
  associate_public_ip_address = true
  user_data                   = local.cloud_init

  root_block_device {
    volume_size = var.ebs_volume_size
    volume_type = var.ebs_volume_type
  }

  dynamic "credit_specification" {
    for_each = local.is_burstable ? [1] : []
    content {
      cpu_credits = var.enable_unlimited_credits ? "unlimited" : "standard"
    }
  }

  tags = merge(var.labels, {
    Name = var.instance_name
  })
}
