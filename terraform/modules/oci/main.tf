terraform {
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = "~> 6.0"
    }
  }
}

locals {
  ad_name = data.oci_identity_availability_domains.ads.availability_domains[0].name

  cloud_init = templatefile("${path.module}/cloud-init.yml.tmpl", {
    ssh_public_key = var.ssh_public_key
  })
}

# --- Networking ---

resource "oci_core_vcn" "benchmark" {
  compartment_id = var.compartment_id
  display_name   = "${var.instance_name}-vcn"
  cidr_blocks    = ["10.0.0.0/16"]
  freeform_tags  = var.labels
}

resource "oci_core_internet_gateway" "benchmark" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.benchmark.id
  display_name   = "${var.instance_name}-igw"
  enabled        = true
  freeform_tags  = var.labels
}

resource "oci_core_route_table" "benchmark" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.benchmark.id
  display_name   = "${var.instance_name}-rt"
  freeform_tags  = var.labels

  route_rules {
    destination       = "0.0.0.0/0"
    network_entity_id = oci_core_internet_gateway.benchmark.id
  }
}

resource "oci_core_security_list" "benchmark" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.benchmark.id
  display_name   = "${var.instance_name}-sl"
  freeform_tags  = var.labels

  # SSH access from allowed IPs
  dynamic "ingress_security_rules" {
    for_each = var.allowed_ssh_ips
    content {
      protocol  = "6" # TCP
      source    = ingress_security_rules.value
      stateless = false

      tcp_options {
        min = 22
        max = 22
      }
    }
  }

  # ICMP from allowed IPs
  dynamic "ingress_security_rules" {
    for_each = var.allowed_ssh_ips
    content {
      protocol  = "1" # ICMP
      source    = ingress_security_rules.value
      stateless = false

      icmp_options {
        type = 8 # Echo request
      }
    }
  }

  # Allow all outbound
  egress_security_rules {
    protocol    = "all"
    destination = "0.0.0.0/0"
    stateless   = false
  }
}

resource "oci_core_subnet" "benchmark" {
  compartment_id             = var.compartment_id
  vcn_id                     = oci_core_vcn.benchmark.id
  display_name               = "${var.instance_name}-subnet"
  cidr_block                 = "10.0.1.0/24"
  route_table_id             = oci_core_route_table.benchmark.id
  security_list_ids          = [oci_core_security_list.benchmark.id]
  prohibit_public_ip_on_vnic = false
  freeform_tags              = var.labels
}

# --- Compute Instance ---

resource "oci_core_instance" "benchmark" {
  compartment_id      = var.compartment_id
  availability_domain = local.ad_name
  display_name        = var.instance_name
  shape               = var.instance_shape
  freeform_tags       = var.labels

  shape_config {
    ocpus         = var.instance_ocpus
    memory_in_gbs = var.instance_memory_gb
  }

  source_details {
    source_type             = "image"
    source_id               = data.oci_core_images.ubuntu.images[0].id
    boot_volume_size_in_gbs = var.boot_volume_size_gb
  }

  create_vnic_details {
    subnet_id        = oci_core_subnet.benchmark.id
    assign_public_ip = true
    display_name     = "${var.instance_name}-vnic"
    freeform_tags    = var.labels
  }

  metadata = {
    ssh_authorized_keys = var.ssh_public_key
    user_data           = base64encode(local.cloud_init)
  }
}
