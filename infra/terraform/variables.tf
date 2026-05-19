variable "location" {
  type        = string
  description = "Azure region."
  default     = "northeurope"
}

variable "resource_group_name" {
  type    = string
  default = "reedintel-prod-rg"
}

variable "environment" {
  type    = string
  default = "prod"
}

variable "postgres_admin_user" {
  type    = string
  default = "reedadmin"
}

variable "postgres_admin_password" {
  type        = string
  sensitive   = true
  description = "Set via GitHub secret TF_VAR_postgres_admin_password."
}

variable "allowed_admin_ip" {
  type        = string
  description = "Optional: your public IP for local psql access. Leave empty to use Azure Cloud Shell only."
  default     = ""
}

variable "openai_api_key" {
  type      = string
  sensitive = true
  default   = ""
}
