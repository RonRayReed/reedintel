#!/bin/bash
set -e

# Prompt for DB password if not passed as env var
if [ -z "${DB_PASS:-}" ]; then
  read -s -p "Enter your PostgreSQL password (the one you set during setup): " DB_PASS && echo ""
fi

ACR_PASS=$(az acr credential show --name reedintelacr --resource-group reedintel-prod-rg --query "passwords[0].value" -o tsv)
PG_FQDN=$(az postgres flexible-server show --name reedintel-pg-prod --resource-group reedintel-prod-rg --query fullyQualifiedDomainName -o tsv)

echo "Credentials fetched. PG host: $PG_FQDN"

# --- Worker: set registry, enable internal ingress, set all env vars ---
az containerapp registry set \
  --name reedintel-worker \
  --resource-group reedintel-prod-rg \
  --server reedintelacr.azurecr.io \
  --username reedintelacr \
  --password "$ACR_PASS"

az containerapp ingress enable \
  --name reedintel-worker \
  --resource-group reedintel-prod-rg \
  --type internal \
  --target-port 8000 \
  --transport http

az containerapp update \
  --name reedintel-worker \
  --resource-group reedintel-prod-rg \
  --image reedintelacr.azurecr.io/reedintel-worker:latest \
  --set-env-vars "DATABASE_HOST=$PG_FQDN" DATABASE_NAME=reedintel DATABASE_USER=reedadmin "DATABASE_PASSWORD=$DB_PASS" DATABASE_SSLMODE=require RUN_MODE=continuous

echo "Worker updated."

# --- Dashboard: delete and recreate with BACKEND_URL ---
az containerapp delete --name reedintel-dashboard --resource-group reedintel-prod-rg --yes 2>/dev/null || true

az containerapp create \
  --name reedintel-dashboard \
  --resource-group reedintel-prod-rg \
  --environment reedintel-prod-cae \
  --image reedintelacr.azurecr.io/reedintel-dashboard:latest \
  --registry-server reedintelacr.azurecr.io \
  --registry-username reedintelacr \
  --registry-password "$ACR_PASS" \
  --cpu 0.5 --memory 1.0Gi \
  --min-replicas 1 --max-replicas 1 \
  --ingress external --target-port 80 \
  --env-vars BACKEND_URL=http://reedintel-worker

echo ""
echo "=============================="
echo "  Dashboard URL:"
az containerapp show --name reedintel-dashboard --resource-group reedintel-prod-rg --query "properties.configuration.ingress.fqdn" -o tsv
echo "=============================="
