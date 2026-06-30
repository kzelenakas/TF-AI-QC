# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TF AI-QC is an internal appraisal quality control tool for True Footage. Appraisers upload UAD 3.6 reports (XML or PDF); the system runs compliance checks, scores report quality, manages a revision workflow, and tracks appraiser performance over time.

The spec is the authoritative source: `docs/superpowers/specs/2026-06-25-uad-qc-tool-design.md`. Read it before implementing anything non-trivial.

## Infrastructure

**Current target stack: Railway + Supabase + Bubble + Ollama.** GCP stack deprecated. See `docs/STACK-GUIDE.md` for full rationale.

| Component | Stack |
|---|---|
| Backend hosting | Railway (FastAPI) |
| AI model (local) | Ollama — `glm-4.7-flash` (Railway service) |
| Database | Supabase (PostgreSQL 15) |
| File storage | Cloudflare R2 |
| Auth | Bubble native auth (passed as token to backend) |
| Frontend | Bubble (no React — UI lives in True Footage Bubble app) |
| Email | Resend |
| Background jobs | Railway cron + background workers |
| CI/CD | Railway auto-deploy from GitHub `main` |
| Agent harness | Ruflo (`npx ruflo@latest init` already run) |

Bubble OMS integration is **Phase 1**, not Phase 3 — frontend lives in Bubble from day one.

## Commands

Backend (once scaffold exists):
```powershell
# Run backend locally
uvicorn app.main:app --reload

# Run migrations
alembic upgrade head

# Seed rules table
python -m app.db.seed_rules

# Admin CLI (post-deploy)
python -m app.cli create-admin
python -m app.cli seed-rules
python -m app.cli check-health
```

Ollama (local dev):
```powershell
# Pull model
ollama pull glm-4.7-flash

# Start Ollama server
ollama serve
```

Tests:
```powershell
# Run all backend tests
pytest

# Run a single test file
pytest backend/tests/unit/test_auth.py -v
```

## Architecture

### Backend (`backend/app/`)

```
core/        — config, supabase client, R2 client, auth dependencies (Bubble token verify)
api/routes/  — auth, reports, revisions, rules, coaching, internal (cron jobs), integrations
models/      — SQLAlchemy 2.x ORM: User, Report, QCResult, QCFlag, Revision, RevisionResponse, Rule
services/
  ingest/    — xml_parser.py, pdf_extractor.py, extractor_factory.py → all output ReportData
  rules/     — engine.py (two-pass), base_rule.py, uad_format/, gse/, uspap/, quality_scorer.py
  workflow/  — state_machine.py (report lifecycle transitions)
  coaching/  — pattern_detector.py, report_generator.py, recommendations.py
  storage.py — Cloudflare R2 wrapper (upload, signed URLs)
  qc_service.py — orchestrates ingest → rule engine → DB save
  notifications.py — Resend email (plain requests, no SDK)
  privacy/pii_scrubber.py — strips PII before any text reaches Ollama
  integrations/bubble_client.py — True Footage OMS sync (primary integration)
  ai/ollama_client.py — Ollama API wrapper (glm-4.7-flash, fallback to Claude API if unreachable)
db/          — Alembic migrations, seed_rules.py
```

### Frontend

**No React.** Frontend is built in Bubble — pages live inside the True Footage Bubble app.
Bubble calls the FastAPI backend via Bubble's API Connector plugin.
Auth token from Bubble passed as `Authorization: Bearer` header on all API calls.

### Rule Engine (two-pass)

**Pass 1 — Hard Compliance:** UAD formatting rules, required field population, GSE overlays (Fannie Mae, Freddie Mac, FHA, VA), USPAP rules. Any failure blocks the report.

**Pass 2 — Quality Scoring (0–100):** Five weighted sub-scorers: Comparables (30%), Adjustments (25%), Market Analysis (20%), Narrative (15%), Reconciliation (10%). Narrative scoring calls Ollama (`glm-4.7-flash`) with PII-scrubbed text. Falls back to Claude API if Ollama unreachable.

Rules are stored in the `rules` DB table and cached in the engine. Admins can toggle rules on/off without a deploy.

### Report Lifecycle

```
submitted → qc_running → qc_complete → approved
                                     → revision_requested → resubmitted → qc_running (loop)
```

Transitions are role-enforced: only reviewers/admins can approve or request revision; only the original uploader can resubmit. Each transition is logged to Railway application logs (no PII in logs).

## Data Model Notes

- `reports.file_url` stores the R2 object key, not a signed URL. Generate 15-minute presigned URLs at request time.
- `qc_results.raw_flags` is JSONB — full engine output, schema can evolve without migration.
- `run_number` increments on each resubmission — full USPAP audit trail.
- `rules.config` is JSONB — stores adjustable thresholds (e.g., net adjustment threshold) so rules are tunable without code changes.

## Security Constraints

These are not suggestions — appraisal reports contain GLBA-protected NPI.

- **PII scrubber is mandatory** before any text reaches Ollama or any external AI API. `pii_scrubber.py` replaces names → `[PERSON]`, addresses → `[ADDRESS]`, SSNs/loan numbers → `[REDACTED]`, dollar amounts → `[VALUE]`.
- **Signed URLs only.** Report files in Cloudflare R2 are never publicly accessible. Always return 15-minute presigned URLs, never permanent links. Log signed URL generation.
- **No PII in logs.** Log only: `user_id`, `report_id`, `file_type`, `file_size`, `timestamp`, `action`, `result`. Never log file content, addresses, names, or financial figures.
- **File validation is server-side.** Check magic bytes (not just filename/extension) to confirm XML or PDF. Reject everything else.
- **CORS is restricted** to the True Footage Bubble domain — no wildcard `*` origins.
- **All credentials** come from Railway environment variables in production. Local dev uses `.env.local` (gitignored).
- **Audit logging** is required for every access to NPI data (upload, view, download, export, admin actions). Minimum 3-year retention.
- **Bubble auth tokens** verified on every request — backend extracts `user_id` and `role` from token claims.

## Context Files

Place reference documents here before implementing rules — the engine reads them during build sessions:

```
context/guidelines/uspap/    — current USPAP edition
context/guidelines/gse/      — Fannie Mae B4-1, Freddie Mac 5600, FHA 4000.1, VA Ch.11
context/rule-references/uad-3.6/  — UAD Appendix D, MISMO XSD schema
context/sample-reports/1004/ — redacted/synthetic URAR samples only (no real borrower data)
data-sources/bubble-oms/     — Bubble API config (gitignored)
```

## Build Session Model

Sessions are sequential — each builds on the last. Use `claude-opus-4-8` with Extended Thinking for implementation sessions.

Reference: `docs/STACK-GUIDE.md` — authoritative stack decisions, rationale, cost estimates, and session build order.

**Deprecated:** `docs/GOOGLE-CLOUD-GUIDE.md` (GCP stack — do not use). `prompts/PLAYBOOK.md` (Railway v1 — superseded).
