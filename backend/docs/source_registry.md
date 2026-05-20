# Reed Intel Source Registry

| Source | Type | City | Country | Auth | Frequency | Status |
|--------|------|------|---------|------|-----------|--------|
| ProZorro | Procurement | Kyiv | Ukraine | No | 30 min | Active |
| MTender | Procurement | Chisinau | Moldova | No | 60 min | Skeleton |
| ANAF | Tax | Bucharest | Romania | Yes | Daily | Skeleton |
| ONRC | Registry | Bucharest | Romania | Yes | Daily | Planned |
| Lviv Open Data | Municipal | Lviv | Ukraine | No | Daily | Active |
| Odesa Open Data | Municipal | Odesa | Ukraine | No | Daily | Active |
| Ukrainian Sea Ports Authority | Port | Odesa | Ukraine | No | Daily | Planned |
| Lviv IT Cluster | Industry | Lviv | Ukraine | No | Weekly | RSS |
| OpenDataBot | Company enrichment | Ukraine | Ukraine | API Key | On-demand | Skeleton |

## Adding a New Source
1. Add a row to the `sources` table via an Alembic migration or directly in the database
2. Create a connector in `worker/src/connectors/`
3. Import and call it in `worker/src/main.py`
4. Add an n8n schedule node in `prozorro_monitor.json` or create a new workflow
