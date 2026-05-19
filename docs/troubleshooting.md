# Reed Intel Troubleshooting Guide

| Problem | Likely Cause | Fix |
|---------|-------------|-----|
| Terraform fails authentication | `AZURE_CREDENTIALS` secret malformed or expired | Recreate service principal, update GitHub secret |
| PostgreSQL connection refused | Firewall rule missing or IP changed | Update `allowed_admin_ip` and rerun Terraform |
| n8n opens without login prompt | Basic auth env vars not configured | Set `N8N_BASIC_AUTH_PASSWORD` and redeploy |
| Worker runs but no records appear | Connector endpoint changed or source API unavailable | Check logs, test endpoint manually, update connector |
| Too many duplicate companies | Entity resolution thresholds too low | Raise `automatic_match` threshold to 95+ in `entity_resolution.py` |
| AI drafts contain unsupported claims | Prompt too loose or insufficient structured facts | Use stricter system prompt, require source-bound drafting |
| Costs rise unexpectedly | Containers scaled too high or logs retained too long | Set `max_replicas`, reduce retention, review Azure Cost Management |
| ProZorro returns 0 tenders | Offset parameter or API version changed | Check ProZorro API docs, test `BASE_URL` manually |
| Container App won't start | Image not pushed to ACR or wrong image tag | Re-run `deploy-worker.yml`, check ACR for latest tag |

## Checking Logs
```bash
# Stream worker logs
az containerapp logs show \
  --name reedintel-worker \
  --resource-group reedintel-prod-rg \
  --follow

# Stream n8n logs
az containerapp logs show \
  --name reedintel-n8n \
  --resource-group reedintel-prod-rg \
  --follow
```

## Resetting a Stuck Container App
```bash
az containerapp revision restart \
  --name reedintel-worker \
  --resource-group reedintel-prod-rg
```
