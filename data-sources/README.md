# Data Sources Folder

External data connections and integration configs. Each subfolder maps to a data source the QC tool can pull from.

## Folders

| Folder | Purpose | Status |
|---|---|---|
| `bubble-oms/` | True Footage order management system (Bubble.io) | Phase 8 |
| `mls/` | MLS data feeds for comp verification (future) | Post-beta |
| `public-records/` | County assessor / public record data (future) | Post-beta |
| `market-data/` | Market trend data sources (future) | Post-beta |

## bubble-oms/
Place `config.md` here with:
- Bubble app name
- API endpoint base URL
- Notes on available data types

⚠️ Never store API tokens in this folder. Use environment variables (BUBBLE_API_TOKEN).

## Future Data Sources (Post-Beta)
- **MLS data** — for comp validation (verify reported sale prices against MLS records)
- **FEMA flood maps** — for flood zone validation
- **County assessor** — for GLA and site size cross-check
- **PropMix / Profet API** — market trend data if partnership established
