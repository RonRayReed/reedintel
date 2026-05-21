#!/bin/bash
set -e

# Prompt for DB password if not passed as env var
if [ -z "${DB_PASS:-}" ]; then
  read -s -p "Enter your PostgreSQL password (the one you set during setup): " DB_PASS && echo ""
fi

ACR_PASS=$(az acr credential show --name reedintelacr --resource-group reedintel-prod-rg --query "passwords[0].value" -o tsv)
PG_FQDN=$(az postgres flexible-server show --name reedintel-pg-prod --resource-group reedintel-prod-rg --query fullyQualifiedDomainName -o tsv)
ENV_DOMAIN=$(az containerapp env show --name reedintel-prod-cae --resource-group reedintel-prod-rg --query "properties.defaultDomain" -o tsv)
BACKEND_URL="https://reedintel-backend.internal.$ENV_DOMAIN"

echo "Credentials fetched."
echo "  PG host      : $PG_FQDN"
echo "  Backend URL  : $BACKEND_URL"

# --- [1/4] Build all images in ACR first ---
echo ""
echo "[1/4] Building images in ACR..."
az acr build --registry reedintelacr --image reedintel-backend:latest  ./backend
az acr build --registry reedintelacr --image reedintel-worker:latest   ./worker
az acr build --registry reedintelacr --image reedintel-dashboard:latest ./frontend
echo "  Images built."

# --- [2/4] Worker: background ingestion job (no ingress needed) ---
echo ""
echo "[2/4] Updating worker..."
az containerapp registry set \
  --name reedintel-worker \
  --resource-group reedintel-prod-rg \
  --server reedintelacr.azurecr.io \
  --username reedintelacr \
  --password "$ACR_PASS"

az containerapp update \
  --name reedintel-worker \
  --resource-group reedintel-prod-rg \
  --image reedintelacr.azurecr.io/reedintel-worker:latest \
  --set-env-vars "DATABASE_HOST=$PG_FQDN" DATABASE_NAME=reedintel DATABASE_USER=reedadmin "DATABASE_PASSWORD=$DB_PASS" DATABASE_SSLMODE=require RUN_MODE=continuous

echo "  Worker updated."

# --- [3/4] Backend: FastAPI API server (internal ingress, port 8000) ---
echo ""
echo "[3/4] Deploying backend API..."
BACKEND_EXISTS=$(az containerapp show --name reedintel-backend --resource-group reedintel-prod-rg --query name -o tsv 2>/dev/null || echo "")

if [ -z "$BACKEND_EXISTS" ]; then
  az containerapp create \
    --name reedintel-backend \
    --resource-group reedintel-prod-rg \
    --environment reedintel-prod-cae \
    --image reedintelacr.azurecr.io/reedintel-backend:latest \
    --registry-server reedintelacr.azurecr.io \
    --registry-username reedintelacr \
    --registry-password "$ACR_PASS" \
    --cpu 0.5 --memory 1.0Gi \
    --min-replicas 1 --max-replicas 2 \
    --ingress internal --target-port 8000 --allow-insecure \
    --env-vars \
      "DATABASE_HOST=$PG_FQDN" \
      DATABASE_NAME=reedintel \
      DATABASE_USER=reedadmin \
      "DATABASE_PASSWORD=$DB_PASS" \
      DATABASE_SSLMODE=require
else
  az containerapp registry set \
    --name reedintel-backend \
    --resource-group reedintel-prod-rg \
    --server reedintelacr.azurecr.io \
    --username reedintelacr \
    --password "$ACR_PASS"

  az containerapp update \
    --name reedintel-backend \
    --resource-group reedintel-prod-rg \
    --image reedintelacr.azurecr.io/reedintel-backend:latest \
    --set-env-vars "DATABASE_HOST=$PG_FQDN" DATABASE_NAME=reedintel DATABASE_USER=reedadmin "DATABASE_PASSWORD=$DB_PASS" DATABASE_SSLMODE=require
fi
echo "  Backend updated."

# --- [4/4] Dashboard: React frontend (external ingress, port 80) ---
echo ""
echo "[4/4] Deploying dashboard..."
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
  --env-vars "BACKEND_URL=$BACKEND_URL"

echo ""
echo "=============================================="
echo "  REED INTEL — APPS DEPLOYED"
echo "=============================================="
echo "  Dashboard : https://$(az containerapp show --name reedintel-dashboard --resource-group reedintel-prod-rg --query "properties.configuration.ingress.fqdn" -o tsv)"
echo "  Backend   : $BACKEND_URL (internal only)"
echo "=============================================="
