output "postgres_fqdn" {
  value = azurerm_postgresql_flexible_server.pg.fqdn
}

output "storage_account_name" {
  value = azurerm_storage_account.storage.name
}

output "key_vault_name" {
  value = azurerm_key_vault.kv.name
}

output "n8n_url" {
  value = "https://${azurerm_container_app.n8n.latest_revision_fqdn}"
}

output "acr_login_server" {
  value = azurerm_container_registry.acr.login_server
}

output "resource_group" {
  value = azurerm_resource_group.rg.name
}
