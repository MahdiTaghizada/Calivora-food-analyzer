variable "resource_group_name" { type = string }
variable "location" { type = string }
variable "name_prefix" { type = string }
variable "tags" { type = map(string) }

resource "random_string" "suffix" {
  length  = 5
  special = false
  upper   = false
}

resource "azurerm_container_registry" "this" {
  name                          = replace("${var.name_prefix}${random_string.suffix.result}", "-", "")
  resource_group_name           = var.resource_group_name
  location                      = var.location
  sku                           = "Standard"
  admin_enabled                 = false
  public_network_access_enabled = true
  anonymous_pull_enabled        = false
  tags                          = var.tags
}

output "id" { value = azurerm_container_registry.this.id }
output "login_server" { value = azurerm_container_registry.this.login_server }
