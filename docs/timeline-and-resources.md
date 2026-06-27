# TF AI-QC — Timeline & Resources

**As of:** June 27, 2026
**Mandate deadline:** November 2, 2026 (UAD 3.6 required for all GSE loans)

---

## Timeline Overview

Total estimated duration: **18–22 weeks** from IT/legal approval to full deployment.

The UAD 3.6 mandate on November 2, 2026 is the hard deadline. Working backward from that date, IT/legal approval needs to happen **no later than late July 2026** to leave adequate build and testing time.

---

## Phase Breakdown

### Phase 0 — IT/Legal Approval
**Duration:** 2–4 weeks
**Target completion:** Late July 2026

- IT reviews hosting options and approves infrastructure
- Legal reviews and executes required vendor data processing agreements
- Budget approved for infrastructure and development costs
- Hosting path confirmed (GCP internal vs. Railway external)

**Blocker:** Nothing else starts until this is complete.

---

### Phase 1 — Architecture & Environment Setup
**Duration:** 1–2 weeks

- Development environment configured (GCP project or Railway project)
- GitHub repositories organized and access granted to any developers
- Database schema designed and provisioned
- Authentication configured (Google SSO or equivalent)
- PII scrubbing layer implemented and tested (required before any real data touches the system)
- CI/CD pipeline set up (automated testing and deployment)

**Deliverable:** Empty but fully functional infrastructure. Developers can deploy code.

---

### Phase 2 — Core Rules Engine & Report Ingestion
**Duration:** 4–5 weeks

- UAD 3.6 XML parser built (ingests reports from appraisal software)
- Fannie Mae / Freddie Mac UAD Compliance API integrated (covers 709+ hard rules automatically)
- USPAP compliance rule layer built
- Internal True Footage quality rules implemented (comp selection, adjustments, market analysis, narrative, reconciliation)
- Quality scoring algorithm built
- All rules tested against known-good and known-bad sample reports

**Deliverable:** Engine that accepts a UAD 3.6 report and returns a structured findings report with pass/fail on every rule.

---

### Phase 3 — Web Application (Reviewer Interface)
**Duration:** 3–4 weeks

- Reviewer dashboard: upload report, view findings, approve/override each finding
- Revision request generator: auto-drafts revision requests from failed checks
- Report detail view: side-by-side rule findings with report content
- Admin panel: manage rules, view system status

**Deliverable:** Working web application reviewers can use to process reports end-to-end.

---

### Phase 4 — Appraiser Portal & Workflow
**Duration:** 2–3 weeks

- Appraiser-facing view: receive revision requests, submit corrections
- Workflow routing: report moves through QA → revision → resubmission states
- Email or Slack notifications on status changes

**Deliverable:** Full round-trip workflow from upload to revision resolution.

---

### Phase 5 — Performance Dashboard & Coaching Tools
**Duration:** 2–3 weeks

- Appraiser performance dashboard: findings by appraiser over time, recurring issue patterns
- Trend analysis: which rules fail most often, which appraisers have recurring issues
- Export: findings data exportable to CSV for further analysis

**Deliverable:** Management and QDS visibility into quality trends across the team.

---

### Phase 6 — Pilot Testing
**Duration:** 2–3 weeks

- Internal pilot with 2–3 QA reviewers and a set of historical reports
- Compare AI findings against past manual review results
- Tune quality scoring weights based on reviewer feedback
- Identify edge cases and fix
- Document final user workflow

**Deliverable:** Validated system ready for full deployment.

---

### Phase 7 — Full Deployment
**Duration:** 1 week

- All QA reviewers onboarded
- Appraiser access configured
- Live with real reports
- IT/security final sign-off

**Deliverable:** System live and in production before November 2, 2026 mandate.

---

## Calendar View

| Phase | Duration | Target Window |
|-------|----------|---------------|
| 0 — IT/Legal Approval | 2–4 wks | July 2026 |
| 1 — Setup | 1–2 wks | Late July–Early August |
| 2 — Rules Engine | 4–5 wks | August 2026 |
| 3 — Reviewer UI | 3–4 wks | September 2026 |
| 4 — Appraiser Portal | 2–3 wks | Early October 2026 |
| 5 — Performance Dashboard | 2–3 wks | Mid October 2026 |
| 6 — Pilot Testing | 2–3 wks | Late October 2026 |
| 7 — Full Deployment | 1 wk | **November 1, 2026** |

---

## Resources Required

### People

| Role | Responsibility | Source |
|------|---------------|--------|
| **Kevin Zelenakas (QDS)** | Domain expert, rule definitions, test validation, project direction | Internal |
| **Full-Stack Developer (1)** | Backend API, rules engine, database, infrastructure | Hire / contract |
| **Frontend Developer (1)** | Web application UI — reviewer dashboard, appraiser portal | Hire / contract (or same as above if full-stack) |
| **IT Administrator** | GCP/infrastructure setup, SSO configuration, security review | Internal IT |
| **Legal Counsel** | Vendor DPA review, GLBA compliance sign-off | Internal legal |

**Note:** One strong full-stack developer can handle both backend and frontend, extending the timeline by 2–3 weeks but reducing cost significantly. Two developers (one back, one front) is the faster path.

---

### Development Tools

| Tool | Purpose | Cost |
|------|---------|------|
| GitHub (private repos) | Source code, version control | Free (existing) |
| VSCode + Claude Code | Development environment + AI assistance | Free / existing subscription |
| Claude Code (Sonnet/Opus) | AI-assisted development | Existing subscription |
| Postman or REST Client (VSCode) | API testing | Free |
| GitHub Actions | CI/CD pipeline (automated testing + deployment) | Free tier sufficient |

---

### Infrastructure — Option A (GCP Internal)

| Service | Purpose | Est. Monthly Cost |
|---------|---------|------------------|
| Google Cloud Run | Application hosting | $50–$150 |
| Cloud SQL (PostgreSQL) | Database | $75–$150 |
| Google Cloud Storage | Appraisal file storage | $10–$30 |
| Vertex AI | AI quality analysis | $50–$200 (usage-based) |
| Cloud DLP API | PII scrubbing | $10–$30 |
| Firebase Authentication | User login | Free tier sufficient |
| **Total** | | **$195–$560/month** |

---

### Infrastructure — Option B (External)

| Service | Purpose | Est. Monthly Cost |
|---------|---------|------------------|
| Railway (Pro) | App + database hosting | $20–$100 |
| Cloudflare R2 | File storage | $5–$15 |
| Anthropic Claude API | AI quality analysis | $50–$300 (usage-based) |
| **Total** | | **$75–$415/month** |

---

### External APIs (Both Options)

| API | Purpose | Cost |
|-----|---------|------|
| Fannie Mae UAD Compliance API | 709 URAR hard rules validation | Free (registration required) |
| Freddie Mac UAD Compliance API | Parallel GSE validation | Free (registration required) |

---

### One-Time Development Costs

| Item | Estimate |
|------|---------|
| Full-stack developer (contract, 4–5 months) | $40,000–$80,000 |
| Frontend developer (contract, 3–4 months, if separate) | $25,000–$50,000 |
| Infrastructure setup and configuration | $500–$2,000 |
| **Total one-time** | **$40,000–$132,000** |

---

## Critical Path Items

1. **IT/legal approval** — nothing starts without it
2. **Developer hire/contract** — sourcing takes time; start immediately after approval
3. **Fannie Mae UAD Compliance API registration** — register now, do not wait
4. **PII scrubber** — must be built and validated before any real appraisal data enters the system

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| IT/legal approval delayed past July | Medium | High | Brief IT/legal now; present both options simultaneously |
| Developer not available in time | Medium | High | Begin sourcing immediately; consider two-developer team to compress timeline |
| Fannie Mae API access delayed | Low | High | Register for API access this week |
| PII scrubber has gaps | Low | Critical | Use Google Cloud DLP (proven) rather than custom-built |
| UAD 3.6 rule changes before mandate | Low | Medium | Pin to GSE API — rules update automatically |
| Scope creep delays core features | Medium | Medium | Phase 5 (dashboard) is deferrable; Phases 1–4 are the MVP |
