terraform {
  required_version = ">= 1.6.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

provider "azurerm" {
  features {}
}

variable "subscription_id" {
  type      = string
  sensitive = true
  default   = null
}
variable "tenant_id" {
  type      = string
  sensitive = true
  default   = null
}
variable "client_id" {
  type      = string
  sensitive = true
  default   = null
}
variable "client_secret" {
  type      = string
  sensitive = true
  default   = null
}
variable "location" {
  type    = string
  default = "westeurope"
}
variable "project_name" {
  type    = string
  default = "calivora"
}
variable "environment" {
  type    = string
  default = "prod"
}

resource "random_string" "suffix" {
  length  = 6
  special = false
  upper   = false
}

resource "azurerm_resource_group" "state" {
  name     = "${var.project_name}-${var.environment}-tfstate-rg"
  location = var.location
}

resource "azurerm_storage_account" "state" {
  name                            = substr("${var.project_name}${var.environment}tf${random_string.suffix.result}", 0, 24)
  resource_group_name             = azurerm_resource_group.state.name
  location                        = azurerm_resource_group.state.location
  account_tier                    = "Standard"
  account_replication_type        = "LRS"
  min_tls_version                 = "TLS1_2"
  https_traffic_only_enabled      = true
  allow_nested_items_to_be_public = false
  shared_access_key_enabled       = true
  public_network_access_enabled   = true

  blob_properties {
    versioning_enabled = true
    container_delete_retention_policy { days = 7 }
    delete_retention_policy { days = 7 }
  }
}

resource "azurerm_storage_container" "tfstate" {
  name                  = "tfstate"
  storage_account_name  = azurerm_storage_account.state.name
  container_access_type = "private"
}

output "resource_group_name" { value = azurerm_resource_group.state.name }
output "storage_account_name" { value = azurerm_storage_account.state.name }
output "container_name" { value = azurerm_storage_container.tfstate.name }
