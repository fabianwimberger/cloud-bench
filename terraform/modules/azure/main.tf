terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }
}

locals {
  # Azure VM names: alphanumeric and hyphens only
  safe_name = replace(var.instance_name, "_", "-")

  cloud_init = templatefile("${path.module}/cloud-init.yml.tmpl", {})

  image_reference = var.instance_arch == "arm64" ? {
    publisher = "Canonical"
    offer     = "ubuntu-24_04-lts"
    sku       = "server-arm64"
    version   = "latest"
    } : {
    publisher = "Canonical"
    offer     = "ubuntu-24_04-lts"
    sku       = "server"
    version   = "latest"
  }
}

resource "azurerm_resource_group" "benchmark" {
  name     = local.safe_name
  location = var.region
  tags     = var.tags
}

resource "azurerm_virtual_network" "benchmark" {
  name                = "${local.safe_name}-vnet"
  address_space       = ["10.0.0.0/16"]
  location            = azurerm_resource_group.benchmark.location
  resource_group_name = azurerm_resource_group.benchmark.name
  tags                = var.tags
}

resource "azurerm_subnet" "benchmark" {
  name                 = "internal"
  resource_group_name  = azurerm_resource_group.benchmark.name
  virtual_network_name = azurerm_virtual_network.benchmark.name
  address_prefixes     = ["10.0.1.0/24"]
}

resource "azurerm_network_security_group" "benchmark" {
  name                = "${local.safe_name}-nsg"
  location            = azurerm_resource_group.benchmark.location
  resource_group_name = azurerm_resource_group.benchmark.name
  tags                = var.tags
}

resource "azurerm_network_security_rule" "ssh" {
  name                        = "allow-ssh"
  priority                    = 100
  direction                   = "Inbound"
  access                      = "Allow"
  protocol                    = "Tcp"
  source_port_range           = "*"
  destination_port_range      = "22"
  source_address_prefixes     = var.allowed_ssh_ips
  destination_address_prefix  = "*"
  resource_group_name         = azurerm_resource_group.benchmark.name
  network_security_group_name = azurerm_network_security_group.benchmark.name
}

resource "azurerm_public_ip" "benchmark" {
  name                = "${local.safe_name}-pip"
  location            = azurerm_resource_group.benchmark.location
  resource_group_name = azurerm_resource_group.benchmark.name
  allocation_method   = "Static"
  sku                 = "Standard"
  tags                = var.tags
}

resource "azurerm_network_interface" "benchmark" {
  name                = "${local.safe_name}-nic"
  location            = azurerm_resource_group.benchmark.location
  resource_group_name = azurerm_resource_group.benchmark.name
  tags                = var.tags

  ip_configuration {
    name                          = "internal"
    subnet_id                     = azurerm_subnet.benchmark.id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = azurerm_public_ip.benchmark.id
  }
}

resource "azurerm_network_interface_security_group_association" "benchmark" {
  network_interface_id      = azurerm_network_interface.benchmark.id
  network_security_group_id = azurerm_network_security_group.benchmark.id
}

resource "azurerm_linux_virtual_machine" "benchmark" {
  name                = local.safe_name
  resource_group_name = azurerm_resource_group.benchmark.name
  location            = azurerm_resource_group.benchmark.location
  size                = var.instance_type
  admin_username      = "ubuntu"

  network_interface_ids = [
    azurerm_network_interface.benchmark.id,
  ]

  admin_ssh_key {
    username   = "ubuntu"
    public_key = var.ssh_public_key
  }

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = var.disk_type
    disk_size_gb         = var.disk_size_gb
  }

  source_image_reference {
    publisher = local.image_reference.publisher
    offer     = local.image_reference.offer
    sku       = local.image_reference.sku
    version   = local.image_reference.version
  }

  custom_data = base64encode(local.cloud_init)

  tags = var.tags
}
