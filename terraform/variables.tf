variable "subscription_id" {
  description = "Azure subscription ID."
  type        = string
  sensitive   = true
}

variable "tenant_id" {
  description = "Microsoft Entra tenant ID."
  type        = string
  sensitive   = true
}

variable "client_id" {
  description = "Service principal application/client ID."
  type        = string
  sensitive   = true
}

variable "client_secret" {
  description = "Service principal client secret."
  type        = string
  sensitive   = true
}

variable "location" {
  description = "Azure region."
  type        = string
  default     = "westeurope"
}

variable "project_name" {
  description = "Short project name used in resource names."
  type        = string
  default     = "calivora"
}

variable "environment" {
  description = "Deployment environment."
  type        = string
  default     = "prod"
}

variable "kubernetes_version" {
  description = "Optional AKS Kubernetes version. Leave null for the platform default."
  type        = string
  default     = null
  nullable    = true
}

variable "node_vm_size" {
  description = "AKS system node VM size."
  type        = string
  default     = "Standard_D4s_v5"
}

variable "node_min_count" {
  description = "Minimum AKS system node count."
  type        = number
  default     = 2
}

variable "node_max_count" {
  description = "Maximum AKS system node count."
  type        = number
  default     = 5
}

variable "app_image" {
  description = "Container image for the Calivora API."
  type        = string
  default     = ""
}

variable "llm_provider" {
  type    = string
  default = "anthropic"
}

variable "llm_model" {
  type    = string
  default = "claude-sonnet-4-6"
}

variable "anthropic_api_key" {
  type      = string
  default   = ""
  sensitive = true
}

variable "openai_api_key" {
  type      = string
  default   = ""
  sensitive = true
}

variable "google_api_key" {
  type      = string
  default   = ""
  sensitive = true
}

variable "usda_api_key" {
  type      = string
  default   = ""
  sensitive = true
}

variable "offline_mode" {
  type    = bool
  default = false
}
