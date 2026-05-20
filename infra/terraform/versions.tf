terraform {
  required_version = ">= 1.6.0"

  backend "azurerm" {
    resource_group_name  = "reedintel-tfstate-rg"
    storage_account_name = "reedinteltfstate"
    container_name       = "tfstate"
    key                  = "prod.terraform.tfstate"
  }

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.110"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}
