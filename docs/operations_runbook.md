# Reed Intel Operations Runbook

## Daily Checklist
- [ ] Check Azure Container Apps logs for worker failures
- [ ] Review `source_records` count by source for the prior 24 hours
- [ ] Review `editorial_queue` sorted by `confidence_score DESC`
- [ ] Approve, reject, or flag items for research
- [ ] Confirm no API credentials have expired
- [ ] Check PostgreSQL CPU/storage in Azure Monitor
- [ ] Review high-value procurement alerts (value > 250,000)

## Weekly Checklist
- [ ] Run duplicate company detection → send to human review
- [ ] Generate weekly city heatmaps by event count, sector, value
- [ ] Export top procurement events by city and sector
- [ ] Prepare editorial story queue for each city desk
- [ ] Publish the weekly regional business intelligence report
- [ ] Backup PostgreSQL and export CSV of core tables

## Monthly Checklist
- [ ] Refresh all chamber and membership lists
- [ ] Re-score company confidence rankings
- [ ] Review source reliability and API coverage
- [ ] Run relationship graph updates
- [ ] Update sector taxonomies
- [ ] Review Azure costs and remove unused resources
- [ ] Audit AI drafts for hallucinations and editorial accuracy

## Applying the Database Schema (First Time)
Use **Azure Cloud Shell** — no IP or local tools needed:
1. Open portal.azure.com → click the Cloud Shell icon (top bar)
2. Run:
```bash
psql "host=reedintel-pg-prod.postgres.database.azure.com port=5432 dbname=reedintel user=reedadmin sslmode=require"
```
3. Paste the contents of `database/schema.sql` then `database/seed_reference_data.sql`

## Key Azure Resources
| Resource | Name |
|----------|------|
| Resource Group | reedintel-prod-rg |
| PostgreSQL | reedintel-pg-prod |
| Storage | reedintelprodsa |
| Key Vault | reedintel-prod-kv |
| Container App Env | reedintel-prod-cae |
| n8n | reedintel-n8n |
| Worker | reedintel-worker |
| Log Analytics | reedintel-prod-law |

## Useful Queries
```sql
-- Records ingested last 24h by source
SELECT source_name, COUNT(*) FROM source_records
WHERE fetched_at > NOW() - INTERVAL '24 hours'
GROUP BY source_name ORDER BY COUNT(*) DESC;

-- High-priority editorial queue
SELECT title, city, sector, confidence_score, created_at FROM editorial_queue
WHERE status = 'new' ORDER BY confidence_score DESC LIMIT 20;

-- Weekly procurement totals
SELECT city, sector, COUNT(*), SUM(value_amount) FROM procurement_events
WHERE publication_date > NOW() - INTERVAL '7 days'
GROUP BY city, sector ORDER BY COUNT(*) DESC;
```
