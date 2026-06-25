# TF AI-QC — True Footage Appraisal Quality Control Platform

AI-powered QC tool for UAD 3.6 residential appraisal reports. Built for True Footage's internal review workflow.

## What It Does

- Accepts UAD 3.6 appraisal reports in XML or PDF format
- Runs automated hard compliance checks (UAD formatting, GSE overlays, USPAP)
- Scores report quality (comparables, adjustments, market analysis, narrative, reconciliation)
- Manages revision request workflow between appraisers and reviewers
- Tracks appraiser performance over time for coaching and training

## Stack

- **Backend:** Python / FastAPI
- **Frontend:** React / TypeScript / Tailwind
- **Database:** PostgreSQL (Railway managed)
- **File Storage:** Cloudflare R2
- **AI:** Anthropic Claude API
- **Deployment:** Railway

## Project Structure

```
TF AI-QC/
├── backend/          # FastAPI backend
│   ├── app/
│   │   ├── api/      # Route handlers
│   │   ├── core/     # Auth, config, dependencies
│   │   ├── db/       # Migrations
│   │   ├── models/   # SQLAlchemy ORM models
│   │   └── services/ # Business logic (ingest, rules, workflow, coaching)
│   └── tests/
├── frontend/         # React frontend
│   └── src/
│       ├── components/  # appraiser/, reviewer/, admin/, shared/
│       ├── pages/
│       ├── hooks/
│       └── types/
├── context/          # Reference docs (UAD spec, GSE guidelines, sample reports)
├── data-sources/     # External integration configs (Bubble OMS, MLS, etc.)
├── docs/
│   ├── superpowers/specs/  # Design specs
│   ├── training/           # Coaching examples
│   └── api/                # API documentation
└── prompts/          # Cowork build playbook and session prompts
    └── PLAYBOOK.md   # Start here
```

## Getting Started

See `prompts/PLAYBOOK.md` for the full build playbook with session-by-session prompts.

## Design Spec

`docs/superpowers/specs/2026-06-25-uad-qc-tool-design.md`

## Environment Variables

See `backend/.env.example` (created in Session 0).

Key variables:
- `DATABASE_URL` — PostgreSQL connection string
- `SECRET_KEY` — JWT signing key
- `ANTHROPIC_API_KEY` — Claude API for quality scoring
- `CLOUDFLARE_R2_*` — File storage credentials
- `BUBBLE_API_TOKEN` — True Footage OMS integration (Phase 8)

## ⚠️ Security Notes

- Never commit `.env` files — they are gitignored
- Never add real appraisal reports to `context/sample-reports/` — use redacted/synthetic samples only
- API keys go in environment variables only
