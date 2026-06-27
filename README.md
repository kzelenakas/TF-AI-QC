# TF AI-QC — True Footage Appraisal Quality Control Platform

AI-powered QC tool for UAD 3.6 residential appraisal reports. Built for True Footage's internal review workflow.

## Table of Contents

- [What It Does](#what-it-does)
- [Stack](#stack)
- [Project Structure](#project-structure)
- [Documentation](#documentation)
- [Getting Started](#getting-started)
- [Security Notes](#security-notes)

---

## What It Does

- Accepts UAD 3.6 appraisal reports in XML or PDF format
- Runs automated compliance checks against Fannie Mae and Freddie Mac UAD Compliance APIs (709+ URAR rules)
- Scores report quality across five dimensions: comparable selection, adjustments, market analysis, narrative, reconciliation
- Generates structured revision requests from failed checks
- Manages revision workflow between appraisers and QA reviewers
- Tracks appraiser performance trends over time for coaching and training

---

## Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python / FastAPI |
| Frontend | React / TypeScript / Tailwind CSS |
| Database | PostgreSQL |
| File Storage | Cloudflare R2 |
| AI | Anthropic Claude API |
| Deployment | Railway (pending IT/legal hosting decision) |

---

## Project Structure

```
TF-AI-QC/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── api/                # Route handlers
│   │   ├── core/               # Auth, config, dependencies
│   │   ├── db/                 # Migrations
│   │   ├── models/             # SQLAlchemy ORM models
│   │   └── services/           # Rules engine, scoring, workflow, coaching
│   └── tests/
├── frontend/                   # React frontend
│   └── src/
│       ├── components/         # appraiser/, reviewer/, admin/, shared/
│       ├── pages/
│       ├── hooks/
│       └── types/
├── context/                    # Reference docs (UAD spec, GSE guidelines)
├── data-sources/               # External integration configs
├── docs/                       # Project documentation
│   ├── it-legal-brief.md       # Hosting decision brief for IT and legal
│   ├── project-synopsis.md     # Project overview and business case
│   ├── timeline-and-resources.md  # Build phases, timeline, cost estimates
│   ├── dev-tools-and-stack.md  # Full technology and AI options reference
│   ├── APP-STACK-AND-SECURITY.md  # Security architecture
│   ├── SETUP-GUIDE.md          # Developer setup instructions
│   └── superpowers/specs/      # Design specifications
└── prompts/                    # Build playbook and session prompts
    ├── PLAYBOOK.md             # Start here — ordered build sessions
    └── sessions/               # Session-by-session prompts
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [IT/Legal Brief](docs/it-legal-brief.md) | Hosting options, data flow, compliance posture, approvals required |
| [Project Synopsis](docs/project-synopsis.md) | Problem statement, features, business impact, success criteria |
| [Timeline & Resources](docs/timeline-and-resources.md) | Build phases, calendar, people, infrastructure costs |
| [Dev Tools & Stack](docs/dev-tools-and-stack.md) | Technology choices, AI options, rules engine, PII scrubbing |
| [App Stack & Security](docs/APP-STACK-AND-SECURITY.md) | Security architecture and GLBA compliance approach |
| [Setup Guide](docs/SETUP-GUIDE.md) | Developer environment setup |
| [Build Playbook](prompts/PLAYBOOK.md) | Ordered session-by-session build instructions |

---

## Getting Started

See `prompts/PLAYBOOK.md` for the full build playbook.

```powershell
# Clone the repo
git clone https://github.com/kzelenakas/TF-AI-QC.git
cd TF-AI-QC

# Backend
pip install -r backend/requirements.txt
cp backend/.env.example backend/.env   # fill in credentials

# Frontend
npm install --prefix frontend

# Run locally
docker compose up db                   # start database
uvicorn app.main:app --reload          # start backend
npm run dev --prefix frontend          # start frontend
```

---

## Security Notes

- **Never commit `.env` files** — gitignored by default
- **Never add real appraisal reports** to `context/` — use redacted or synthetic samples only
- **NPI handling** — all appraisal data must pass through the PII scrubber before reaching any AI service
- **API keys** — environment variables only, never hardcoded
