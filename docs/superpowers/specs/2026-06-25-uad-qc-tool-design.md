# TF AI-QC Tool — Design Specification
**Date:** 2026-06-25  
**Project:** True Footage AI-Powered Appraisal QC Platform  
**Status:** Approved for Implementation Planning

---

## 1. Overview

A browser-based QC tool for True Footage's internal use, enabling staff appraisers to submit UAD 3.6 appraisal reports and QC reviewers to flag compliance issues, request revisions, and track appraiser performance over time. The tool is appraiser/firm-first — built for the *producer* of appraisals, not the lender/AMC reviewer. This is a meaningful gap in the current market (HomeVision, Profet.ai both serve lenders/AMCs).

**Competitive context:**
- [HomeVision MIRA](https://homevision.co/mira-appraisal-qc) — lender/AMC-facing, enterprise, SOC 2, ~60 days to implement
- [Profet.ai](https://www.profet.ai/profet-review) — lender/AMC-facing, broader suite including order management + data analytics

**Our differentiation:** Appraiser-first UX, USPAP-first compliance framing, coaching/training layer for appraiser development, and native integration path to True Footage's Bubble.io order management system.

---

## 2. Tech Stack

| Layer | Choice | Rationale |
|---|---|---|
| Backend | FastAPI (Python) | Excellent for document processing pipelines, XML/PDF libraries, Claude API integration |
| Frontend | React + TypeScript | Component-driven UI, strong ecosystem, role-based rendering |
| Database | PostgreSQL | Relational integrity for audit trail, JSONB for flexible rule output |
| File Storage | Cloudflare R2 | S3-compatible, no egress fees, keeps files out of Postgres |
| Auth | JWT with role claims | Stateless, scalable to 100+ appraisers |
| AI | Anthropic Claude API | Quality analysis, commentary evaluation, future revision drafting |
| Deployment | Railway (beta) | Managed Postgres, CI/CD, HTTPS out of the box, ~1 hour to live |
| Future integration | Bubble.io REST API | True Footage OMS — pull orders, sync report status |

---

## 3. System Architecture

```
┌─────────────────────────────────────────────┐
│              React Frontend                  │
│  Appraiser Portal | Reviewer Dashboard       │
│  Report Upload | QC Results | Revision UI    │
└────────────────────┬────────────────────────┘
                     │ HTTPS / REST
┌────────────────────▼────────────────────────┐
│             FastAPI Backend                  │
│                                              │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐  │
│  │ Ingest   │  │  Rule    │  │ Workflow  │  │
│  │ Engine   │  │  Engine  │  │  Manager  │  │
│  │XML + PDF │  │UAD 3.6   │  │Revisions  │  │
│  └──────────┘  └──────────┘  └───────────┘  │
│                                              │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐  │
│  │  Auth    │  │  Claude  │  │  Export   │  │
│  │  (JWT)   │  │  AI API  │  │PDF/Report │  │
│  └──────────┘  └──────────┘  └───────────┘  │
└────────────────────┬────────────────────────┘
                     │
┌────────────────────▼────────────────────────┐
│         PostgreSQL (Railway managed)         │
│  Users | Reports | QC Results | Revisions   │
│  File Storage: Cloudflare R2 (XML/PDF)      │
└─────────────────────────────────────────────┘
```

---

## 4. Core Modules

### 4.1 Ingest Engine

Handles two input formats, outputs a normalized `ReportData` object either way:

- **XML path:** Parses UAD 3.6 XML directly into structured field objects. Fast, precise. This is the preferred path.
- **PDF path:** Uses `pdfplumber` to extract text, then a field-mapping layer locates UAD fields by position/label. Flags low-confidence extractions for manual review. PDF layout varies by software (TOTAL, ACI, ClickForms) — this path requires ongoing maintenance as new layouts emerge.

Output: normalized `ReportData` object with all UAD fields regardless of source format.

### 4.2 Rule Engine (Two-Pass)

**Pass 1 — Hard Compliance (pass/fail gates):**
- UAD field formatting rules (date formats, abbreviations, checkbox values per UAD 3.6 spec)
- Required field population by form type (1004, 1073, 1025, 2055)
- GSE-specific overlays: Fannie Mae SEL requirements, Freddie Mac bulletins, FHA/VA addenda
- USPAP compliance flags (scope of work, certifications, limiting conditions)
- Any failure in Pass 1 blocks the report from proceeding

**Pass 2 — Quality Scoring (0–100):**
- Comp selection logic (proximity, time, GLA similarity, sale price range)
- Market condition support adequacy
- Adjustment grid consistency and reasonableness
- Commentary depth analysis (Claude-assisted NLP)
- Output: overall score + category subscores (Comps, Adjustments, Market, Commentary, Condition)

### 4.3 Workflow Manager

Report lifecycle:
```
Submitted → QC Running → QC Complete
  ├── [All Pass 1 clear + quality ≥ threshold] → Approved
  └── [Fail or quality flags] → Revision Requested → Resubmitted → QC Running (loop)
```

- Revision requests are threaded per flagged issue
- Appraiser sees exactly which field/section needs fixing and why
- Each resubmission increments `run_number` for full audit trail
- Reviewer can waive any flag with a documented reason

### 4.4 Authentication & Roles

Three roles via JWT claims:

| Role | Permissions |
|---|---|
| `appraiser` | Submit reports, view own QC results, respond to revisions |
| `reviewer` | View all reports, override/waive flags, write revision requests, approve reports |
| `admin` | User management, rule configuration, system reporting |

---

## 5. Data Model

### Core Tables

**`users`**  
`id, email, name, role, license_number, license_state, active, created_at`

**`reports`**  
`id, uploader_id (FK), file_url (R2), file_type (xml|pdf), form_type (1004|1073|1025|2055), subject_address, status, submitted_at, completed_at`

**`qc_results`**  
`id, report_id (FK), run_number, hard_pass (bool), quality_score (0-100), raw_flags (JSONB), created_at`

**`qc_flags`**  
`id, qc_result_id (FK), category (compliance|quality), severity (fail|warning|info), field_name, rule_code, message, gse_reference, status (open|waived|resolved)`

**`revisions`**  
`id, report_id (FK), flag_id (FK), created_by (FK reviewer), message, status (open|responded|closed), created_at`

**`revision_responses`**  
`id, revision_id (FK), created_by (FK appraiser), message, resubmission_file_url, created_at`

**`rules`**  
`id, rule_code (unique), category, severity, description, gse_applicability (array), active, config (JSONB)`

### Design Notes
- `raw_flags` JSONB stores full rule engine output — schema can evolve without data loss
- `rules` table allows toggling rules on/off and adjusting thresholds without a code deploy
- `run_number` provides complete audit trail across resubmissions (USPAP documentation)

---

## 6. User Experience

### Appraiser View
- Login → report queue with status badges (Submitted, In Review, Revision Needed, Approved)
- Drag-drop upload for XML or PDF
- QC runs automatically in background (target: <2 min)
- Revision requests show per-issue with field reference, reviewer note, and response field
- Resubmit directly from the same screen

### Reviewer View
- Dashboard: all reports across all appraisers, filterable by status / appraiser / form type / GSE
- QC results: hard compliance failures at top (red), quality flags below (yellow/blue)
- Click any flag to write a revision request or waive with note
- Approve report when clean

### Admin View
- User management (add, deactivate appraisers)
- Rule configuration (toggle, adjust thresholds)
- Reporting: turnaround times, revision rates by appraiser, common failure categories

---

## 7. Appraiser Performance & Coaching Layer

This differentiates the tool from all current competitors (HomeVision, Profet) — a training asset, not just a compliance gate.

**Per-appraiser dashboards track:**
- Revision rates (overall and by category)
- Common flag categories over time
- Quality score trends
- First-pass approval rates

**Recurring issue detection:**
- System surfaces patterns when an appraiser repeatedly gets flagged in the same category
- Generates coaching opportunity alerts for reviewers/admins

**Cohort benchmarking:**
- Compare individual appraiser metrics against team averages (anonymized)

**Reviewer notes as training data:**
- Every revision request is categorized and stored
- Builds a dataset of team-wide weaknesses over time
- Powers future coaching report exports

---

## 8. Deployment Plan (Beta → Production)

### Beta (Phase 1)
- Deploy to Railway (single service: FastAPI + React served as static files)
- Railway-managed PostgreSQL
- Cloudflare R2 for file storage
- Target: functional beta in 4–6 weeks

### Integration (Phase 2)
- Connect to True Footage's Bubble.io OMS via Bubble's REST Data API
- Pull active orders into report context
- Push QC status back to Bubble on approval

### Scale (Phase 3)
- Extract rule engine as separate service if processing volume demands it
- Add SOC 2 compliance (required for lender clients)
- Consider white-labeling for other appraisal firms

---

## 9. Plugins, Skills & Resources Needed

### Development Resources
- **Python developer** (backend): FastAPI, SQLAlchemy, pdfplumber, lxml for XML parsing
- **React developer** (frontend): TypeScript, role-based routing, file upload UI
- **Can be one full-stack developer** for beta scope

### External Services
| Service | Purpose | Cost Est. |
|---|---|---|
| Railway | Hosting + managed Postgres | ~$20–50/mo (beta) |
| Cloudflare R2 | File storage | ~$0–15/mo (beta) |
| Anthropic Claude API | Quality analysis | Pay per token, ~$50–200/mo est. |
| SendGrid or Resend | Email notifications | Free tier covers beta |

### Cowork Skills (for ongoing development with Claude)
| Skill | Use |
|---|---|
| `superpowers:writing-plans` | Implementation plan (next step) |
| `superpowers:test-driven-development` | Writing tests before code |
| `superpowers:systematic-debugging` | Debugging rule engine logic |
| `superpowers:requesting-code-review` | Code review before merging |
| `awesome-claude-skills:webapp-testing` | Testing the UI with Playwright |
| `awesome-claude-skills:pdf` | PDF extraction work |
| `awesome-claude-skills:xlsx` | Exporting QC reports |

### Reference Tools for Benchmarking
- [HomeVision MIRA Appraisal QC](https://homevision.co/mira-appraisal-qc) — enterprise competitor, lender-facing
- [Profet Review](https://www.profet.ai/profet-review) — competitor with order management integration

### Visual Mockup References (open in browser for review)
- Appraiser upload + queue UI mockup: *[to be generated in visual companion session]*
- Reviewer dashboard + flag UI mockup: *[to be generated in visual companion session]*
- Appraiser coaching dashboard mockup: *[to be generated in visual companion session]*

> **Note:** These mockups can be built in a future session using the visual companion feature. Ask Claude to "show me the appraiser dashboard mockup" to generate interactive wireframes.

---

## 10. UAD 3.6 Rule Engine — Initial Rule Categories

To be built out during implementation, but initial scope covers:

**Formatting Rules (Hard)**
- Date formats (MM/DD/YYYY)
- UAD abbreviation compliance (condition ratings C1–C6, quality Q1–Q6)
- Numeric field ranges and decimal precision
- Required checkbox states by form section

**Population Rules (Hard)**
- All required fields populated per form type
- Addenda references correct
- Signature/certification fields complete

**GSE Overlay Rules (Hard)**
- Fannie Mae: SEL-2021-07 and current selling guide requirements
- Freddie Mac: current seller/servicer guide
- FHA: HUD 4000.1 Handbook requirements
- VA: Lender Handbook Chapter 11

**Quality Rules (Soft)**
- Comp time adjustments present when sales >6 months old
- GLA adjustments within reasonable range
- Market condition commentary matches trend data
- Neighborhood description internally consistent
- Minimum commentary word counts by section

---

*Spec written 2026-06-25. Ready for implementation planning.*
