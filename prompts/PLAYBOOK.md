# TF AI-QC Build Playbook
**Model:** claude-opus-4-8 (use for all implementation sessions)  
**Project:** True Footage Appraisal QC Tool  
**Spec:** `docs/superpowers/specs/2026-06-25-uad-qc-tool-design.md`  
**Last Updated:** 2026-06-30

---

## How to Use This Playbook

Each session below is a self-contained Cowork prompt. Copy it, paste it at the start of a new Cowork session, and Claude will have everything it needs. Sessions are ordered — don't skip ahead, as each builds on the last.

**Before every session:**
1. Switch model to `claude-opus-4-8` in Cowork settings
2. Make sure your TF AI-QC project folder is selected
3. Copy the session prompt below and paste it as your first message

**Token efficiency tips:**
- One session = one focused module. Don't combine phases.
- If a session runs long, end it and start a new one with the "continuation prompt" pattern shown in Phase 1.
- Add reference docs (UAD spec, GSE guidelines) to `context/` folder — Claude will read them when needed rather than loading everything upfront.

---

## Order of Operations

```
Phase 0: Environment Setup (1 session)
    ↓
Phase 1: Foundation — DB + Auth + File Upload (3 sessions)
    ↓
Phase 2: Ingest Engine — XML + PDF (2 sessions)
    ↓
Phase 3: Rule Engine — Compliance + Quality (4 sessions)
    ↓
Phase 4: Workflow Manager — Lifecycle + Revisions (2 sessions)
    ↓
Phase 5: Frontend — Appraiser + Reviewer + Admin (4 sessions)
    ↓
Phase 6: Beta Deployment — Railway + Smoke Tests (1 session)
    ↓
Phase 7: Coaching Layer — Performance + Patterns (2 sessions)
    ↓
Phase 8: Bubble.io Integration (1 session)
```

**Estimated sessions:** 20  
**Estimated calendar time at 2–3 sessions/week:** 8–10 weeks to working beta

---

## Phase 0: Environment Setup

### SESSION 0 — Project Scaffolding & Infrastructure

```
You are helping me build a residential appraisal QC tool called TF AI-QC for True Footage, an appraisal firm. Read the design spec first:

docs/superpowers/specs/2026-06-25-uad-qc-tool-design.md

Then set up the complete project scaffold:

BACKEND (Python/FastAPI):
- Initialize backend/ as a Python project with pyproject.toml or requirements.txt
- Install: fastapi, uvicorn, sqlalchemy, alembic, psycopg2-binary, python-jose[cryptography], passlib[bcrypt], pdfplumber, lxml, boto3 (for Cloudflare R2), anthropic, python-multipart, pydantic-settings
- Create backend/app/main.py with FastAPI app instance, CORS config, and router imports
- Create backend/app/core/config.py using pydantic-settings for environment variables (DATABASE_URL, SECRET_KEY, CLOUDFLARE_R2_BUCKET, CLOUDFLARE_R2_ENDPOINT, ANTHROPIC_API_KEY)
- Create backend/.env.example with all required env vars

FRONTEND (React/TypeScript):
- Initialize frontend/ with Vite + React + TypeScript
- Install: react-router-dom, axios, @tanstack/react-query, zustand, tailwindcss
- Create basic App.tsx with router setup and placeholder routes for /login, /appraiser, /reviewer, /admin
- Configure tailwind.config.ts

DATABASE:
- Set up Alembic for migrations in backend/app/db/
- Create initial migration with all tables from the spec: users, reports, qc_results, qc_flags, revisions, revision_responses, rules
- Include all columns, foreign keys, and indexes

DEPLOYMENT CONFIG:
- Create railway.toml for Railway deployment
- Create Dockerfile for the backend
- Create .gitignore for the full project

After scaffolding, run the backend locally and confirm it starts without errors. Show me the output.
```

---

## Phase 1: Foundation

### SESSION 1A — Database Models & Migrations

```
You are helping me build TF AI-QC, a residential appraisal QC tool. Read the spec:

docs/superpowers/specs/2026-06-25-uad-qc-tool-design.md

The project scaffold is in place. Focus only on this session's task:

Create complete SQLAlchemy ORM models for all database tables. Files go in backend/app/models/:

- user.py — User model with role enum (appraiser, reviewer, admin)
- report.py — Report model with status enum and file_type enum
- qc_result.py — QCResult model with quality_score and raw_flags JSONB
- qc_flag.py — QCFlag model with category, severity, and status enums
- revision.py — Revision and RevisionResponse models
- rule.py — Rule model with gse_applicability array and config JSONB
- __init__.py — exports all models

Then create or update the Alembic migration to match these models exactly. Run `alembic upgrade head` and confirm the migration succeeds. Show me the output.

Use SQLAlchemy 2.x syntax with DeclarativeBase.
```

### SESSION 1B — Authentication System

```
You are helping me build TF AI-QC, a residential appraisal QC tool. Read the spec:

docs/superpowers/specs/2026-06-25-uad-qc-tool-design.md

The database models are complete. Build the authentication system:

Files to create:
- backend/app/core/security.py — JWT token creation/verification, password hashing with passlib
- backend/app/api/routes/auth.py — POST /auth/login (returns JWT), POST /auth/register (admin only), GET /auth/me
- backend/app/core/dependencies.py — get_current_user dependency, role-checking dependencies (require_reviewer, require_admin)

Requirements:
- JWT tokens include: user_id, email, role, exp (24h default)
- Passwords hashed with bcrypt
- Role enforcement: reviewers can access appraiser routes, admins can access all routes
- Return 401 for invalid/expired tokens, 403 for insufficient role

Write unit tests in backend/tests/unit/test_auth.py covering:
- Valid login returns JWT
- Invalid password returns 401
- Expired token returns 401  
- Appraiser token rejected on reviewer-only route

Run tests and show output.
```

### SESSION 1C — File Upload & Cloudflare R2

```
You are helping me build TF AI-QC, a residential appraisal QC tool. Read the spec:

docs/superpowers/specs/2026-06-25-uad-qc-tool-design.md

Auth is working. Build the file upload system:

Files to create:
- backend/app/services/storage.py — R2StorageService class wrapping boto3 S3 client pointed at Cloudflare R2 endpoint. Methods: upload_file(file_bytes, filename, content_type) → url, delete_file(url), generate_presigned_url(url, expiry_seconds)
- backend/app/api/routes/reports.py — POST /reports/upload (multipart, accepts XML and PDF up to 50MB), GET /reports (list for current user, all for reviewer), GET /reports/{id} (with QC results)

Upload endpoint behavior:
1. Validate file type (application/xml, text/xml, application/pdf only)
2. Upload to R2 under path: reports/{user_id}/{date}/{uuid}.{ext}
3. Create Report record in DB with status=submitted
4. Return report_id and status

Write integration test in backend/tests/integration/test_upload.py that uploads a small dummy XML file and confirms the DB record is created.

Note: Use environment variables for R2 config, never hardcode credentials.
```

---

## Phase 2: Ingest Engine

### SESSION 2A — UAD 3.6 XML Parser

```
You are helping me build TF AI-QC, a residential appraisal QC tool. Read the spec:

docs/superpowers/specs/2026-06-25-uad-qc-tool-design.md

Build the XML ingest engine for UAD 3.6 format appraisal reports.

File to create: backend/app/services/ingest/xml_parser.py

The UAD 3.6 XML format uses the MISMO standard. The parser should:
1. Accept raw XML bytes
2. Parse using lxml (not ElementTree — lxml is faster and handles namespaces better)
3. Extract all UAD fields into a normalized ReportData dataclass (define in backend/app/services/ingest/models.py)
4. Handle both UCDP and FNMA XML schema variants
5. Flag fields that are present but empty vs fields that are absent entirely (different QC implications)
6. Return confidence_score (0.0–1.0) indicating parse completeness

ReportData must include these field groups:
- subject_property (address, legal_description, property_type, year_built, gla, site_size, condition, quality)
- contract_info (sale_price, date, seller, buyer, financing_type)
- neighborhood (name, boundaries, built_up, growth, supply_demand, marketing_time, trend)
- site (dimensions, zoning, utilities, off_site_improvements, fema_flood_zone)
- improvements (foundation, exterior, roof, interior, heating, cooling, amenities)
- comparables (list of 3-6 comparable sales, each with address, proximity, sale_price, sale_date, gla, adjustments)
- reconciliation (indicated_value, final_value, value_conclusion)
- certifications (list of certification statements, appraiser_license, supervisor_license)
- raw_fields (dict of all field_name → value for any field not explicitly mapped)

Sample UAD XML, the blank UAD 3.6 form, and the GSE_UAD_3.6.0_v1.3 XSD schema are already in context/rule-references/uad-3.6/ (GSE_UAD_3.6.0_v1.3_schema/, Appendix G-1.xlsx, 36blank.pdf) — read them before writing the parser.

Write unit tests with a minimal valid UAD XML fixture. Run tests and show output.
```

### SESSION 2B — PDF Extractor

```
You are helping me build TF AI-QC, a residential appraisal QC tool. Read the spec:

docs/superpowers/specs/2026-06-25-uad-qc-tool-design.md

The XML parser is complete. Now build the PDF extraction engine.

File to create: backend/app/services/ingest/pdf_extractor.py

PDF appraisal reports come from multiple software packages (TOTAL by a la mode, ACI, ClickForms). Each has slightly different layouts. The extractor should:
1. Accept PDF bytes
2. Use pdfplumber to extract text and table data page by page
3. Use a layout-aware field detection approach: look for label-value pairs by proximity on the page
4. Map extracted text to the same ReportData schema used by the XML parser
5. Assign confidence scores per field (0.0–1.0) based on extraction reliability
6. Flag any field with confidence < 0.7 as "low_confidence" in a separate list
7. Return the same ReportData object as the XML parser — the rule engine should never know the source

Layout profiles to handle:
- TOTAL (a la mode) — most common, 2-page summary + addenda
- Generic UAD-compliant PDF — fallback for unknown software

Create backend/app/services/ingest/extractor_factory.py that:
- Detects file type (XML vs PDF)
- Routes to xml_parser or pdf_extractor
- Returns normalized ReportData either way

Write unit tests with a minimal 2-page test PDF fixture (generate one programmatically using reportlab if needed).
```

---

## Phase 3: Rule Engine

### SESSION 3A — Rule Engine Framework & UAD Formatting Rules

```
You are helping me build TF AI-QC, a residential appraisal QC tool. Read the spec:

docs/superpowers/specs/2026-06-25-uad-qc-tool-design.md

The ingest engine is complete. Build the rule engine framework and first rule set.

Architecture:
- backend/app/services/rules/engine.py — RuleEngine class that:
  - Loads active rules from the DB (or rule config files in context/rule-references/ — see context/rule-references/QC_rules/ for the compliance rule matrix)
  - Runs Pass 1 (hard compliance) then Pass 2 (quality scoring)
  - Returns RuleEngineResult with: hard_pass (bool), quality_score (int 0-100), flags (list of QCFlag-ready dicts)
  - Each flag includes: rule_code, category, severity, field_name, message, gse_reference

- backend/app/services/rules/base_rule.py — BaseRule abstract class with:
  - rule_code, category, severity, description class attributes
  - evaluate(report_data: ReportData) → list[RuleViolation] method
  - gse_applicability list (which GSEs this rule applies to)

UAD Formatting Rules to implement (backend/app/services/rules/uad_format/):
- rule_date_format.py — All dates must be MM/DD/YYYY format
- rule_condition_rating.py — Condition must be C1-C6 only
- rule_quality_rating.py — Quality must be Q1-Q6 only
- rule_required_fields_1004.py — All required fields for Form 1004 must be non-empty
- rule_required_fields_1073.py — Required fields for Form 1073 (condo)
- rule_uad_abbreviations.py — Neighborhood supply/demand, growth, built-up use UAD abbreviations only
- rule_value_range.py — Appraised value must be a positive number

Load rules from files (not just DB) for Phase 3 — we'll wire DB toggle later.

Write unit tests for each rule with passing and failing ReportData fixtures.
```

### SESSION 3B — GSE Overlay Rules

```
You are helping me build TF AI-QC, a residential appraisal QC tool. Read the spec:

docs/superpowers/specs/2026-06-25-uad-qc-tool-design.md

Read context/guidelines/gse/ (Freddie Mac SG 5600-Property guide, UAD 3.6 Supplement, Condition/Quality Rating Definitions, ANSI Z765 square footage standard) and context/rule-references/QC_rules/ (Appendix H-1 and H-2 compliance rule matrices — primary source for these rules) before writing code.

The rule engine framework is in place. Add GSE-specific overlay rules.

Directory: backend/app/services/rules/gse/

Fannie Mae rules (fannie_mae/):
- rule_fnma_comp_count.py — Minimum 3 closed sales, prefer 6 for complex properties
- rule_fnma_comp_time.py — Sales more than 12 months old require explanation
- rule_fnma_comp_proximity.py — Comps beyond 1 mile in urban areas require explanation
- rule_fnma_market_conditions.py — 1004MC form must be complete when market is declining
- rule_fnma_gla_adjustment.py — GLA adjustments must be present if difference >15%
- rule_fnma_net_adjustment.py — Net adjustment should not exceed 15% of comp sale price (warning, not fail)
- rule_fnma_gross_adjustment.py — Gross adjustment should not exceed 25% (warning)

FHA rules (fha/):
- rule_fha_minimum_property.py — Flag if condition is C5 or C6 (requires repair escrow or rejection)
- rule_fha_well_septic.py — Well/septic requires additional certification language
- rule_fha_flood_zone.py — AE/VE flood zones require flood certification note

VA rules (va/):
- rule_va_minimum_property.py — VA MPR compliance flags (similar to FHA but different thresholds)
- rule_va_tidewater.py — Flag if value conclusion is below contract price (Tidewater protocol)

USPAP rules (backend/app/services/rules/uspap/):
- rule_uspap_certification.py — All required USPAP certification statements must be present
- rule_uspap_scope_of_work.py — Scope of work statement must be non-empty
- rule_uspap_limiting_conditions.py — Limiting conditions statement must be present
- rule_uspap_appraiser_license.py — License number and state must be populated and formatted correctly

Each rule must declare its gse_applicability (e.g., ['FNMA', 'FHLMC', 'FHA', 'VA', 'ALL']).

Write unit tests for each rule class. Run tests and show output.
```

### SESSION 3C — Quality Scoring Engine + Claude AI Integration

```
You are helping me build TF AI-QC, a residential appraisal QC tool. Read the spec:

docs/superpowers/specs/2026-06-25-uad-qc-tool-design.md

Hard compliance rules are complete. Now build Pass 2 — the quality scoring engine.

File: backend/app/services/rules/quality_scorer.py

QualityScorer class should:
1. Accept a ReportData object that passed Pass 1
2. Run 5 quality sub-scorers (each 0–100):
   - ComparableQualityScorer — proximity, time, physical similarity, data sources
   - AdjustmentConsistencyScorer — are adjustments directional, bracketed, supported?
   - MarketAnalysisScorer — 1004MC completeness, trend data support, commentary alignment
   - NarrativeQualityScorer — Claude-assisted, see below
   - ReconciliationScorer — is the final value logical given the indicated values?
3. Compute overall quality_score as weighted average:
   - Comparables: 30%
   - Adjustments: 25%
   - Market Analysis: 20%
   - Narrative: 15%
   - Reconciliation: 10%
4. Each sub-score that falls below 70 generates a quality flag (severity=warning)

Claude AI Integration (NarrativeQualityScorer):
- File: backend/app/services/rules/quality_narrative_scorer.py
- Use the Anthropic Python SDK (already installed)
- Send relevant text sections (neighborhood description, market conditions commentary, reconciliation commentary) to Claude
- System prompt: You are an expert appraisal reviewer evaluating UAD appraisal report narrative quality for USPAP compliance and GSE acceptability. Score the following commentary sections on a 0-100 scale based on: specificity (not generic boilerplate), support for value conclusion, market condition analysis depth, and absence of unsupported statements. Return JSON only: {"score": int, "flags": [{"field": str, "issue": str}]}
- Parse JSON response, handle API errors gracefully (fall back to score=50 if Claude unavailable)
- Cache Claude responses by content hash to avoid re-scoring identical text (saves tokens)

IMPORTANT: The Claude API key comes from environment variable ANTHROPIC_API_KEY. Never hardcode it.

Write tests for the rule-based scorers. Mock the Claude API in tests.
```

### SESSION 3D — Rule Admin & DB Integration

```
You are helping me build TF AI-QC, a residential appraisal QC tool. Read the spec:

docs/superpowers/specs/2026-06-25-uad-qc-tool-design.md

The rule engine is complete. Wire it to the database so rules can be toggled by admins.

Tasks:
1. Seed the rules table with all implemented rules (rule_code, category, severity, description, gse_applicability, active=True, config={})
   - Create backend/app/db/seed_rules.py script

2. Update RuleEngine to load active rules from DB on startup, cache them, and refresh cache on rule update

3. Add API routes in backend/app/api/routes/rules.py (admin only):
   - GET /rules — list all rules with active status
   - PATCH /rules/{rule_code} — toggle active, update config thresholds
   - POST /rules/refresh — force cache refresh

4. Wire the ingest → rule engine → QC result pipeline:
   - Create backend/app/services/qc_service.py — QCService class with run_qc(report_id) method that:
     a. Loads report from DB
     b. Downloads file from R2
     c. Runs extractor_factory to get ReportData
     d. Runs RuleEngine on ReportData
     e. Saves QCResult and QCFlag records to DB
     f. Updates report status to qc_complete
   - Add background task: when a report is uploaded, queue run_qc(report_id) using FastAPI BackgroundTasks

5. Add GET /reports/{id}/results endpoint returning full QC results with flags, organized by category and severity

Run the full pipeline end-to-end with a test XML file. Show the QC result output.
```

---

## Phase 4: Workflow Manager

### SESSION 4A — Report Lifecycle & State Machine

```
You are helping me build TF AI-QC, a residential appraisal QC tool. Read the spec:

docs/superpowers/specs/2026-06-25-uad-qc-tool-design.md

The QC engine is wired up. Build the workflow state machine.

File: backend/app/services/workflow/state_machine.py

ReportStateMachine class managing these transitions:
- submitted → qc_running (when QC job starts)
- qc_running → qc_complete (when QC job finishes)
- qc_complete → approved (reviewer approves — only if hard_pass=True)
- qc_complete → revision_requested (reviewer flags issues)
- revision_requested → resubmitted (appraiser responds)
- resubmitted → qc_running (auto-triggers new QC run)

Rules:
- Only reviewers and admins can trigger approved or revision_requested
- Only the original uploader can trigger resubmitted
- Invalid transitions raise WorkflowError (400 response)
- Every transition is logged with timestamp and user_id

API routes to add to backend/app/api/routes/reports.py:
- POST /reports/{id}/approve — reviewer/admin only
- POST /reports/{id}/request-revision — reviewer/admin only (requires body with revision notes)
- POST /reports/{id}/resubmit — appraiser only (requires new file upload)

Email notifications (use Resend or SendGrid via HTTP — no SDK needed for beta):
- On revision_requested: email appraiser with list of revision items
- On resubmitted: email assigned reviewer
- On approved: email appraiser

Create backend/app/services/notifications.py — NotificationService using RESEND_API_KEY env var.

Write integration tests for all valid and invalid transitions.
```

### SESSION 4B — Revision Request System

```
You are helping me build TF AI-QC, a residential appraisal QC tool. Read the spec:

docs/superpowers/specs/2026-06-25-uad-qc-tool-design.md

The state machine is complete. Build the revision request system.

API routes in backend/app/api/routes/revisions.py:

Reviewer endpoints:
- POST /reports/{id}/revisions — create revision request tied to a specific qc_flag_id (optional) or freeform
  Body: { flag_id?: string, message: string, priority: "required"|"recommended" }
- GET /reports/{id}/revisions — list all revisions for a report with responses
- PATCH /revisions/{id} — update revision message or close it (reviewer only)
- POST /qc-flags/{id}/waive — waive a flag with a documented reason (reviewer only)

Appraiser endpoints:
- GET /my/revisions — all open revisions across all their reports
- POST /revisions/{id}/respond — submit response to a revision request
  Body: { message: string } — file resubmission handled separately via /reports/{id}/resubmit
- GET /revisions/{id} — view single revision thread

Revision data model behavior:
- A report can have multiple revisions (one per flag or freeform)
- Each revision has a thread of responses (appraiser ↔ reviewer)
- Closing a revision requires reviewer action
- Report can only be approved when all required revisions are closed

Add revision_count and open_revision_count computed fields to GET /reports/{id} response.

Write integration tests for the revision threading flow: create → respond → close.
```

---

## Phase 5: Frontend

### SESSION 5A — Appraiser Portal

```
You are helping me build TF AI-QC, a residential appraisal QC tool. Read the spec:

docs/superpowers/specs/2026-06-25-uad-qc-tool-design.md

The backend is complete. Build the Appraiser Portal in React/TypeScript.

Files in frontend/src/:

components/appraiser/ReportQueue.tsx — Main appraiser view:
- Table of their submitted reports with columns: subject address, form type, submitted date, status badge, quality score
- Status badges: Submitted (gray), In Review (blue), Revision Needed (orange), Approved (green)
- Click row to open report detail

components/appraiser/ReportUpload.tsx — Upload component:
- Drag-and-drop zone accepting XML and PDF (max 50MB)
- Shows file type detected (XML or PDF) and file name
- Progress indicator during upload
- Error state for invalid file types

components/appraiser/ReportDetail.tsx — Report detail view:
- Subject property info (address, form type, status)
- QC result summary: Pass/Fail badge, quality score gauge (0-100)
- If revision requested: list of revision threads the appraiser needs to respond to
- RevisionThread component: shows reviewer message, response input, submit button

components/appraiser/RevisionThread.tsx — Single revision thread:
- Shows flag reference if tied to a QC flag (field name + rule message)
- Reviewer message
- Appraiser response input
- Submit response button

pages/AppraiserPage.tsx — Layout with tabs: My Reports | Upload New

Use @tanstack/react-query for all API calls. Use zustand for auth state (token + user). Use Tailwind for styling — keep it clean and functional, not fancy.
```

### SESSION 5B — Reviewer Dashboard

```
You are helping me build TF AI-QC, a residential appraisal QC tool. Read the spec:

docs/superpowers/specs/2026-06-25-uad-qc-tool-design.md

Appraiser portal is done. Build the Reviewer Dashboard.

Files in frontend/src/components/reviewer/:

ReportDashboard.tsx — All-reports view:
- Filterable table: filter by status, appraiser name, form type, GSE type, date range
- Columns: appraiser name, subject address, form type, GSE, submitted date, status, quality score, open revisions count
- Sort by any column
- Click row to open review panel

ReportReviewPanel.tsx — Full review panel (right sidebar or full page):
- Subject property summary at top
- QC Results section:
  - Hard Compliance: PASS/FAIL banner. If fail, list each failing flag with field name, rule code, GSE reference
  - Quality Score: visual gauge + category subscores (Comparables, Adjustments, Market, Narrative, Reconciliation)
  - Each flag has: [Write Revision] button and [Waive] button
- Active Revisions section: list of open revision threads with status
- Action buttons: [Approve Report] (only enabled if hard_pass=True and no open required revisions) | [Add Freeform Revision]

components/reviewer/FlagCard.tsx — Individual QC flag:
- Shows severity (red=fail, yellow=warning, blue=info), field name, message, GSE reference
- Inline [Write Revision Request] form (textarea + priority toggle)
- [Waive] button with reason input

components/reviewer/RevisionManager.tsx — Manage all revision threads:
- List of revisions with status (open/responded/closed)
- Click to expand thread and reply or close

pages/ReviewerPage.tsx — Layout: dashboard view + selected report side panel
```

### SESSION 5C — Admin Panel

```
You are helping me build TF AI-QC, a residential appraisal QC tool. Read the spec:

docs/superpowers/specs/2026-06-25-uad-qc-tool-design.md

Build the Admin Panel.

Files in frontend/src/components/admin/:

UserManagement.tsx:
- Table of all users: name, email, role, license number, state, active status
- [Add User] form: email, name, role, license number, license state
- Toggle active/inactive per user
- Change role per user

RuleConfiguration.tsx:
- Table of all QC rules: rule code, category, severity, description, GSE applicability, active toggle
- Toggle rules on/off with confirmation dialog
- Expandable config panel per rule (adjustable thresholds shown as number inputs)
- [Refresh Rule Cache] button

SystemReporting.tsx — Key metrics:
- Total reports: this week / this month / all time
- First-pass approval rate (reports approved without revisions / total)
- Average QC turnaround time
- Average quality score
- Top 5 most common failure flags (by rule code)
- Revision rate by appraiser (table sortable by revision rate)

pages/AdminPage.tsx — Tabbed layout: Users | Rules | Reporting
```

### SESSION 5D — Coaching & Performance Dashboards

```
You are helping me build TF AI-QC, a residential appraisal QC tool. Read the spec:

docs/superpowers/specs/2026-06-25-uad-qc-tool-design.md

Build the Appraiser Performance and Coaching dashboards. This is the feature that differentiates us from HomeVision and Profet.

Backend additions needed first (add to backend/app/api/routes/coaching.py):
- GET /coaching/appraiser/{id}/summary — returns:
  - revision_rate (revisions / reports)
  - quality_score_trend (array of {month, avg_score})
  - first_pass_rate
  - top_flag_categories (top 3 flag categories by frequency)
  - vs_team_avg (comparison of their metrics to team averages, anonymized)
- GET /coaching/team/summary — team-wide metrics for admin/reviewer view
- GET /coaching/patterns — recurring issues: appraisers flagged 3+ times in same category in last 30 days

Frontend components:

components/admin/CoachingDashboard.tsx (admin/reviewer view):
- Team overview: avg quality score, avg revision rate, first-pass rate
- Appraiser list with performance sparklines
- Recurring Issues panel: "3 appraisers flagged for Adjustment Consistency this week" type alerts
- Click appraiser → AppraiserPerformanceCard

components/admin/AppraiserPerformanceCard.tsx:
- Quality score trend chart (last 6 months)
- Category breakdown radar/bar chart (Comps, Adjustments, Market, Narrative, Reconciliation)
- vs. team average comparison
- Recent flag history (last 10 flags across all reports)
- Coaching notes field (reviewer can add private notes visible to admins/reviewers only)

components/appraiser/MyPerformance.tsx (appraiser's own view — anonymized team comparison):
- Their own quality score trend
- Category scores vs. anonymized team average
- "Your strengths" and "Areas to improve" derived from flag history

Add a tab in AppraiserPage.tsx: My Reports | Upload New | My Performance
Add a tab in AdminPage.tsx: Users | Rules | Reporting | Coaching
```

---

## Phase 6: Beta Deployment

### SESSION 6 — Deploy to Railway

```
You are helping me deploy TF AI-QC to Railway for beta testing. Read the spec:

docs/superpowers/specs/2026-06-25-uad-qc-tool-design.md

The full application (backend + frontend) is built. Deploy to Railway:

1. RAILWAY SETUP — verify railway.toml is correct:
   - Backend service: Python, runs uvicorn
   - Frontend: build with npm run build, serve with nginx or caddy
   - PostgreSQL plugin: confirm DATABASE_URL is injected

2. ENVIRONMENT VARIABLES — list all required env vars I need to set in Railway dashboard:
   - DATABASE_URL (auto-provided by Railway Postgres)
   - SECRET_KEY (generate a secure random 32-byte hex)
   - CLOUDFLARE_R2_ENDPOINT
   - CLOUDFLARE_R2_BUCKET
   - CLOUDFLARE_R2_ACCESS_KEY_ID
   - CLOUDFLARE_R2_SECRET_ACCESS_KEY
   - ANTHROPIC_API_KEY
   - RESEND_API_KEY
   - FRONTEND_URL (for CORS)

3. PRE-DEPLOY CHECKLIST — verify:
   - All migrations run cleanly against a fresh DB
   - CORS configured for the Railway frontend URL
   - No hardcoded localhost URLs
   - Rules seeded in DB
   - Admin user can be created via CLI command

4. SMOKE TESTS — after deploy, run these checks:
   - Health check endpoint returns 200
   - Login works with test admin credentials
   - File upload accepts a test XML
   - QC job runs and returns results
   - Reviewer can request a revision
   - Appraiser can respond

Create backend/app/cli.py with commands: create-admin, seed-rules, check-health.
Show me the Railway dashboard environment variable list I need to configure.
```

---

## Phase 7: Coaching Layer

### SESSION 7A — Pattern Detection Engine

```
You are helping me build TF AI-QC, a residential appraisal QC tool. Read the spec:

docs/superpowers/specs/2026-06-25-uad-qc-tool-design.md

Beta is deployed. Add the coaching pattern detection engine.

File: backend/app/services/coaching/pattern_detector.py

PatternDetector class with methods:
- detect_recurring_issues(appraiser_id, lookback_days=30) → list of PatternAlert
  - A pattern = same rule_code flagged 3+ times in lookback period
  - Returns: rule_code, flag_count, category, example_report_ids
- get_appraiser_trends(appraiser_id) → AppraiserMetrics
  - quality_score by month (last 6)
  - revision_rate by month (last 6)
  - category_scores: avg quality subscore per category (Comps, Adjustments, etc.)
  - flag_frequency: count per rule_code, sorted descending
- get_team_benchmarks() → TeamBenchmarks
  - anonymous aggregate: avg quality score, avg revision rate, percentile bands
  - top 10 most common flags team-wide
- compare_to_team(appraiser_id) → AppraiserVsTeam
  - appraiser metrics vs team benchmarks
  - percentile rank for quality score and revision rate

Schedule pattern detection to run nightly:
- Add POST /admin/coaching/run-patterns endpoint (admin only, triggers background job)
- Store PatternAlert records in a new coaching_alerts table
- Send weekly digest email to reviewers: "This week's coaching opportunities"

Add Alembic migration for coaching_alerts table.
```

### SESSION 7B — Coaching Reports Export

```
You are helping me build TF AI-QC, a residential appraisal QC tool. Read the spec:

docs/superpowers/specs/2026-06-25-uad-qc-tool-design.md

Pattern detection is running. Add exportable coaching reports.

Files:
- backend/app/services/coaching/report_generator.py — CoachingReportGenerator with:
  - generate_appraiser_report(appraiser_id, period_start, period_end) → PDF bytes
  - generate_team_report(period_start, period_end) → PDF bytes
  
Report content (use reportlab or weasyprint for PDF generation):
- Appraiser report: name, license, period, quality score trend chart, category breakdown, top 3 improvement areas, specific example flags with recommended reading
- Team report: aggregate stats, top 10 recurring issues team-wide, appraiser ranking table (anonymized for non-admin)

API routes:
- GET /coaching/reports/appraiser/{id}?start=&end= — download PDF (reviewer/admin only)
- GET /coaching/reports/team?start=&end= — download team report (admin only)
- GET /coaching/appraiser/{id}/recommendations — return list of specific training recommendations based on flag history

Training recommendations logic (Claude-assisted):
- Given an appraiser's top 3 recurring flag categories, ask Claude to suggest 2-3 specific USPAP or GSE guideline sections they should review
- System prompt: You are an appraisal education expert. Given these recurring QC issues, suggest specific USPAP sections, Fannie Mae Selling Guide sections, or educational resources the appraiser should review. Return JSON: {"recommendations": [{"issue": str, "resource": str, "section": str}]}
- Cache by flag_category combination to save tokens

Frontend: Add [Download Coaching Report] button to AppraiserPerformanceCard for admins.
```

---

## Phase 8: Bubble.io Integration

### SESSION 8 — Connect to True Footage OMS

```
You are helping me build TF AI-QC, a residential appraisal QC tool. Read the spec:

docs/superpowers/specs/2026-06-25-uad-qc-tool-design.md

Context on our OMS: True Footage uses Bubble.io for order management. Bubble has a REST Data API at https://[app-name].bubbleapps.io/api/1.1/obj/ and a Workflow API at https://[app-name].bubbleapps.io/api/1.1/wf/. We need to link QC results back to orders.

File: backend/app/services/integrations/bubble_client.py

BubbleClient class:
- authenticate with Bubble API token (BUBBLE_API_TOKEN env var)
- get_order(order_id) → dict with order details
- get_orders_by_appraiser(appraiser_email) → list of active orders
- update_order_qc_status(order_id, status, qc_result_url) → bool
- Available Bubble status values to map to: "QC Submitted", "QC In Review", "QC Revision Requested", "QC Approved"

Integration flow:
1. Add optional bubble_order_id field to Report model
2. When report is uploaded, optionally pass bubble_order_id in the request body
3. On each status change in the workflow state machine, call BubbleClient.update_order_qc_status
4. Add GET /integrations/bubble/orders endpoint (reviewer only) — fetches active orders from Bubble so reviewers can associate incoming reports with orders

Add bubble-oms/ context folder docs: place Bubble API token and app name in data-sources/bubble-oms/config.md (gitignored — for reference only).

Environment variables to add: BUBBLE_API_TOKEN, BUBBLE_APP_NAME.

This integration is optional at runtime — if BUBBLE_API_TOKEN is not set, skip silently.
```

---

## Recommended Plugins, Skills, MCPs & Connectors

### Install These Now (High Value)

| Tool | Type | Why | Install |
|---|---|---|---|
| **GitHub** | MCP Connector | Version control for all code — track every session's changes, enable code review, CI/CD triggers | Search MCP registry → "GitHub" |
| **Linear** | MCP Connector | Track build tasks, bugs, and feature requests across sessions. Better than a text file. | Search MCP registry → "Linear" |
| **Slack** | MCP Connector | Get notified when QC jobs complete, errors occur, new reports arrive. Essential for beta. | Search MCP registry → "Slack" |
| **Cloudflare Developer Platform** | MCP Connector | Manage R2 storage buckets, inspect workers, monitor usage directly from Cowork | Already in registry |
| **Supabase** | MCP Connector | If you switch from Railway Postgres to Supabase — gives Claude direct DB access for debugging | Already in registry |

### Install for Specific Phases

| Tool | Type | Phase | Why |
|---|---|---|---|
| **Figma** | MCP Connector | Phase 5 | Design the UI screens before building — export specs directly to Claude | Already in registry |
| **Miro** | MCP Connector | Any | Build architecture diagrams, workflow maps collaboratively | Already in registry |
| **Datadog** | MCP Connector | Phase 6+ | Monitor production errors, API latency, QC job performance | Already in registry |
| **Vercel** | MCP Connector | Phase 6 | If you switch frontend hosting to Vercel — manage deployments from Cowork | Already in registry |
| **Exa** | MCP Connector | Any | Better code docs search than WebSearch — useful when looking up FastAPI or pdfplumber docs | Already in registry |

### Skills to Use Per Phase

| Skill | Phase | Use |
|---|---|---|
| `superpowers:writing-plans` | Now | Turn this playbook into a detailed implementation plan |
| `superpowers:test-driven-development` | 1–4 | Write tests before code for rule engine (critical for correctness) |
| `superpowers:systematic-debugging` | Any | When rule engine gives wrong results |
| `superpowers:requesting-code-review` | End of each phase | Verify work before moving to next phase |
| `superpowers:verification-before-completion` | End of each phase | Confirm each phase is solid |
| `awesome-claude-skills:webapp-testing` | Phase 5–6 | Test UI with Playwright before beta launch |
| `awesome-claude-skills:pdf` | Phase 2 | PDF extraction work and testing |
| `awesome-claude-skills:xlsx` | Phase 7 | Export coaching reports as Excel for Kevin's review |
| `design:design-critique` | Phase 5 | Review UI before shipping to appraisers |
| `design:accessibility-review` | Phase 5 | Ensure UI works for all users |

### What's Missing From the Registry (Build or Find These)

| Gap | Recommendation |
|---|---|
| **GitHub MCP** | Not found in registry search. Install Claude's official GitHub MCP: `npx @anthropic/claude-github-mcp` or use the Cowork plugin install flow to find it. Essential for code management. |
| **Railway MCP** | Railway doesn't have an MCP yet. Use Railway CLI in Bash tool, or monitor via Railway dashboard directly. |
| **Bubble.io MCP** | Bubble doesn't have an MCP. We handle this with direct REST API calls in Phase 8. |
| **Fannie Mae / GSE data feeds** | No MCP available. Selling Guide / UAD reference docs already in `context/guidelines/gse/` and `context/rule-references/QC_rules/`. |
| **UAD 3.6 XML Schema** | Already in `context/rule-references/uad-3.6/GSE_UAD_3.6.0_v1.3_schema/` — Claude will use it when building the XML parser. |

---

## Context Files — Current Inventory

All reference docs are GSE-published guides/samples, already in the repo:

```
context/guidelines/uspap/
  → 2024 USPAP Standards 1-4

context/guidelines/gse/
  → Freddie Mac SG 5600-Property (10-20-2025)
  → UAD 3.6 Supplement (updated 06-03-2026)
  → UAD3.6 Condition and Quality Rating Definitions
  → ANSI Z765-2021 Square Footage standard

context/rule-references/QC_rules/
  → Appendix H-1 Compliance Rules.xlsx
  → Appendix H-2 UAD Compliance Rules Update Report.xlsx
  → primary source for rule engine logic — read first when building Pass 1/Pass 2 rules

context/rule-references/uad-3.6/
  → 36blank.pdf (blank UAD 3.6 form)
  → Appendix A-1 URAR Delivery Specification.xlsx
  → Appendix C-1 URAR Layout/, Appendix E Report Style Guide/, Appendix F-1 URAR Reference Guide/
  → Appendix G-1.xlsx
  → GSE_UAD_3.6.0_v1.3_schema/ (MISMO XSD)

context/sample-reports/1004/
  → GSE Appendix D-1 sample scenarios: SF1-5, SF5A, Condo1-2, Coop1, MH1, 2-4 unit (x2)
  → Appendix D-1 URAR Sample Scenario Matrix v1.3.xlsx
  → uad-sample-scenarios-combined.pdf (large combined file — extract once to text, don't re-feed raw to any AI step)
```

**Privacy note:** All current files are GSE-published reference/sample materials, no real borrower data. Keep it that way — never add real appraisal reports with borrower names, SSNs, or unredacted addresses to the context folder.

---

*Playbook version 1.1 — 2026-06-30*  
*Next step: Run `superpowers:writing-plans` to generate the Phase 0 implementation plan.*
