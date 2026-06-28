# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

TF AI-QC — True Footage AI-Powered Appraisal Quality Control Platform.  
Automates first-pass QA review of UAD 3.6 appraisal reports before submission to UCDP.  
**Hard deadline: November 2, 2026** (UAD 3.6 mandatory for all GSE loans).

## Status

Pre-development. Awaiting IT/legal hosting decision before code starts. Two tracks:

| | Option A (preferred) | Option B |
|---|---|---|
| Hosting | Google Cloud Platform | Railway |
| AI | Vertex AI (Gemini) | Anthropic Claude API |
| Storage | Google Cloud Storage | Cloudflare R2 |
| PII scrubbing | Google Cloud DLP | Microsoft Presidio |
| Auth | Firebase / Google SSO | Auth0 or Clerk |
| Compliance risk | Lower — data stays in GCP tenant | Higher — 3 vendor DPAs required |

## NPI / GLBA Rule — Non-Negotiable

Appraisal reports contain GLBA-protected NPI (borrower name, property address, loan data).

- `reports.pii_scrubbed` must be `true` before any report data reaches an AI API
- Never log or expose `report_data.raw_data` in error messages or external services
- Warn before any workflow that could expose PII to an unvetted external endpoint
- Test only with synthetic or fully redacted report data — never real borrower data

## Stack

Both hosting tracks share the same application stack:

- **Backend:** Python / FastAPI
- **ORM:** SQLAlchemy + Alembic (migrations)
- **Frontend:** React / TypeScript / Tailwind CSS / shadcn/ui
- **Database:** PostgreSQL 15+
- **Background tasks:** Celery
- **XML parsing:** lxml or xmltodict (UAD 3.6 XML)
- **Rules engine:** Zen Engine (Layer 2/3 internal rules — decision table format)

## Database Schema

Initial migration: `db/migrations/001_initial.sql` (written, not yet applied).

### Tables

| Table | Purpose |
|---|---|
| `users` | Internal staff: reviewers, QDS, managers |
| `appraisers` | External appraiser roster, keyed by license + state |
| `reports` | One row per submitted report — status, file ref, PII scrub gate |
| `report_data` | Parsed UAD 3.6 JSONB — **contains PII** |
| `compliance_findings` | One row per rule per report, all 3 layers |
| `quality_scores` | 5-dimension scores per report |
| `revision_requests` | One per review cycle (report can have multiple rounds) |
| `revision_items` | Individual line items within a revision request |
| `appraiser_metrics` | Aggregated performance by period, updated async |
| `audit_log` | Immutable event log — all state changes |

### Key design decisions

- `report_data.raw_data` is JSONB — UAD 3.6 XML structure is too complex for typed columns
- `reports.pii_scrubbed` is the application-level gate before any AI call
- No auth tables — handled by Firebase or Auth0/Clerk depending on hosting track
- No rules tables — Layer 1 rules come from Fannie Mae API; Layer 2/3 live in Zen Engine JSON files in version control
- Alembic manages migrations — never edit the schema directly

## Rules Engine (3 Layers)

**Layer 1 — Fannie Mae / Freddie Mac UAD Compliance API**
- 709 URAR rules + 102 Restricted Report rules — use the API, do not rebuild
- Free, requires registration: singlefamily.fanniemae.com
- Updated automatically by Fannie Mae — register before development starts

**Layer 2 — USPAP + TF Internal Rules (Zen Engine)**
- Decision table format — rules authored as JSON/YAML, version-controlled
- Kevin can add/modify rules without touching code
- GitHub: github.com/gorules/zen

**Layer 3 — LLM Quality Scoring**
- Subjective dimensions: comparable selection, adjustment support, market analysis, narrative quality, reconciliation
- PII scrubber runs first — mandatory
- Results stored in `compliance_findings` with `ai_generated = true`

## Quality Scoring Dimensions

Reports are scored 0–100 across 5 dimensions, stored in `quality_scores`:

1. Comparable selection
2. Adjustment support
3. Market analysis
4. Narrative quality
5. Reconciliation

## Domain Rules for AI Assistance

When writing code or reviewing findings for this project:

1. Lead with GLBA/NPI compliance — flag before tone or code quality
2. Never invent USPAP, Fannie Mae, Freddie Mac, HUD, FHA, VA, or USDA citations
3. Automated findings are tools supporting — not replacing — the licensed appraiser's judgment
4. TF AI-QC does not produce value opinions and does not submit to UCDP
5. Push back if a proposed approach would expose NPI to an unvetted service

## Key Docs (this folder)

- `docs/project-synopsis.md` — full problem statement and success criteria
- `docs/it-legal-brief.md` — hosting decision brief for IT/legal approvers
- `docs/timeline-and-resources.md` — critical path and deadlines
- `docs/dev-tools-and-stack.md` — full stack reference with library choices
- `db/migrations/001_initial.sql` — PostgreSQL initial migration
