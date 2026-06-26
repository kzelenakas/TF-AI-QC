# TF AI-QC — App Stack, Alternatives & Data Security
**Version:** 1.0 — 2026-06-25

---

## ⚠️ Critical Security Notice — Read First

Appraisal reports processed by this system contain **Non-Public Personal Information (NPI)** protected under the **Gramm-Leach-Bliley Act (GLBA)** and **USPAP Confidentiality (Ethics Rule)**. This includes:

- Borrower names, Social Security Numbers, addresses
- Property values, loan amounts, financial terms
- Client/lender identity
- Appraiser license numbers and certifications

**Every technology choice below has been evaluated against these requirements.** Where a service touches report data, the security posture and data handling agreement requirements are noted explicitly.

---

## SECTION 1 — App Stack with Alternatives

---

### 1. Code Editor / IDE

| | Primary | Alternative 1 | Alternative 2 |
|---|---|---|---|
| **App** | VS Code | Cursor | JetBrains PyCharm + WebStorm |
| **Cost** | Free | Free / $20/mo Pro | $24.90/mo bundled |
| **Website** | code.visualstudio.com | cursor.com | jetbrains.com |
| **Why primary** | Industry standard, free, excellent Python + React support, massive extension library | | |
| **Why alt** | Cursor = AI-native editor (good for non-developers). JetBrains = enterprise-grade, may already be approved at True Footage | | |
| **Data risk** | None — local editor only, no data leaves machine | Cursor sends code snippets to AI (configure to disable for sensitive files) | None — local only |
| **Company approval notes** | Widely approved everywhere | Check if AI features are allowed under company AI policy | Common in enterprise environments |

---

### 2. Version Control / Code Repository

| | Primary | Alternative 1 | Alternative 2 |
|---|---|---|---|
| **App** | GitHub (github.com) | GitLab | Azure DevOps |
| **Cost** | Free (private repos) | Free | Free with Microsoft 365 |
| **Website** | github.com | gitlab.com | dev.azure.com |
| **Why primary** | Industry standard, best CI/CD integrations, GitHub MCP available for Cowork | | |
| **Why alt** | GitLab = more enterprise features on free tier, self-hostable. Azure DevOps = likely already approved if company uses Microsoft 365 | | |
| **Data risk** | Code only — NO appraisal data ever goes here (enforced by .gitignore) | Same | Same |
| **Company approval notes** | Most companies allow GitHub for private repos | Strong choice if company prefers EU data residency | Best choice if Microsoft shop |

---

### 3. App Hosting (Backend)

| | Primary | Alternative 1 | Alternative 2 |
|---|---|---|---|
| **App** | Railway | Render | Microsoft Azure App Service |
| **Cost** | ~$5–20/mo | Free tier / ~$7/mo | Pay-as-you-go (~$15–50/mo) |
| **Website** | railway.app | render.com | azure.microsoft.com |
| **Why primary** | Fastest setup, managed Postgres included, simple CI/CD, ideal for beta | | |
| **Why alt** | Render = very similar to Railway, slightly cheaper. Azure = enterprise-grade, likely pre-approved, SOC 2 Type II certified | | |
| **Data risk** | ⚠️ Report files processed in memory here — must enable encryption at rest and HTTPS | Same | Azure has GLBA-compliant configurations available |
| **Company approval notes** | Small/startup friendly | Small/startup friendly | **Best choice if company has existing Azure agreement** |
| **SOC 2** | Not certified | Not certified | ✅ SOC 2 Type II |
| **BAA available** | No | No | Yes (HIPAA/financial compliance) |

**Recommendation if company requires enterprise compliance: Azure App Service.**

---

### 4. Database

| | Primary | Alternative 1 | Alternative 2 |
|---|---|---|---|
| **App** | Railway PostgreSQL | Supabase | Azure Database for PostgreSQL |
| **Cost** | Included with Railway | Free tier / $25/mo | ~$25–75/mo |
| **Website** | railway.app | supabase.com | azure.microsoft.com |
| **Why primary** | Bundled with hosting, zero config | | |
| **Why alt** | Supabase = excellent developer tools, built-in auth. Azure = enterprise, GLBA-compliant, matches Azure hosting | | |
| **Data risk** | ⚠️ Contains metadata (appraiser names, subject addresses, QC results) — must enable encryption at rest | Same — enable encryption | ✅ Encryption at rest by default |
| **SOC 2** | No | SOC 2 Type II ✅ | SOC 2 Type II ✅ |
| **Company approval** | Beta only | Mid-market option | **Best for enterprise** |

---

### 5. File Storage (Appraisal Report Files)

**This is the highest-risk component — XML and PDF files containing full NPI are stored here.**

| | Primary | Alternative 1 | Alternative 2 |
|---|---|---|---|
| **App** | Cloudflare R2 | AWS S3 | Azure Blob Storage |
| **Cost** | Free up to 10GB / $0.015/GB after | $0.023/GB + requests | $0.018/GB |
| **Website** | cloudflare.com/r2 | aws.amazon.com/s3 | azure.microsoft.com |
| **Why primary** | No egress fees, S3-compatible API, fast | | |
| **Why alt** | AWS S3 = industry standard for secure file storage, GLBA-compliant configurations. Azure Blob = matches Azure stack, GLBA-compliant | | |
| **Data risk** | ⚠️ Full NPI files stored here | ⚠️ Same — but mature compliance tooling | ✅ Same — enterprise compliance tooling |
| **Encryption at rest** | ✅ AES-256 by default | ✅ AES-256 by default | ✅ AES-256 by default |
| **SOC 2** | SOC 2 Type II ✅ | SOC 2 Type II ✅ | SOC 2 Type II ✅ |
| **GLBA-ready** | Partial — review DPA | ✅ Yes with proper config | ✅ Yes with proper config |
| **Company approval** | Good for beta | **Best choice for compliance** | Best if Azure stack |

---

### 6. AI / Quality Scoring Engine

**This is the most sensitive component from a data privacy perspective.**  
The narrative quality scorer sends appraisal text to an external AI API. See Section 2 for the privacy architecture that mitigates this risk.

| | Primary | Alternative 1 | Alternative 2 |
|---|---|---|---|
| **App** | Anthropic Claude API | Azure OpenAI Service | AWS Bedrock (Claude) |
| **Cost** | ~$50–150/mo | ~$50–200/mo | ~$50–150/mo |
| **Website** | console.anthropic.com | azure.microsoft.com/ai | aws.amazon.com/bedrock |
| **Why primary** | Best reasoning quality for appraisal analysis, fastest setup | | |
| **Why alt** | Azure OpenAI = same GPT-4 class models inside Microsoft's enterprise security boundary. AWS Bedrock = runs Claude inside your AWS account — data never leaves AWS | | |
| **Data risk** | ⚠️ Sends text to Anthropic's API — see Section 2 for PII scrubbing architecture | ⚠️ Sends text to Microsoft — BAA available | ✅ Data stays in your AWS account |
| **BAA / DPA** | DPA available — request at anthropic.com/legal | ✅ BAA available for enterprise | ✅ Data residency controls built in |
| **SOC 2** | SOC 2 Type II ✅ | SOC 2 Type II ✅ | SOC 2 Type II ✅ |
| **Company approval** | Review with legal | **Best if company already uses Azure** | **Best if company already uses AWS** |

**⚠️ Important:** Before going to production, get a Data Processing Agreement (DPA) signed with whichever AI provider you use. Anthropic has one available. This is required for GLBA compliance when NPI touches the API.

---

### 7. Email Notifications

| | Primary | Alternative 1 | Alternative 2 |
|---|---|---|---|
| **App** | Resend | SendGrid (Twilio) | AWS SES |
| **Cost** | Free up to 3,000/mo | Free up to 100/day | $0.10/1,000 emails |
| **Website** | resend.com | sendgrid.com | aws.amazon.com/ses |
| **Why primary** | Developer-friendly, generous free tier, excellent deliverability | | |
| **Why alt** | SendGrid = industry standard, widely approved. AWS SES = cheapest at scale, matches AWS stack | | |
| **Data risk** | Low — emails contain revision request text only, no full report data | Same | Same |
| **Company approval** | Generally approved | **Most widely pre-approved** | Good if AWS stack |

---

### 8. Project Management / Task Tracking

| | Primary | Alternative 1 | Alternative 2 |
|---|---|---|---|
| **App** | Linear | Jira (Atlassian) | Azure DevOps Boards |
| **Cost** | Free up to 250 issues | Free up to 10 users | Free with Microsoft 365 |
| **Website** | linear.app | atlassian.com/jira | dev.azure.com |
| **Why primary** | Fast, clean UI, excellent for small teams, Cowork MCP available | | |
| **Why alt** | Jira = most widely approved enterprise tool. Azure DevOps = free if company has M365 | | |
| **Data risk** | None — task descriptions only, no report data | None | None |
| **Company approval** | Startup/SMB friendly | **Most likely already approved** | Best if M365 shop |

---

### 9. Monitoring & Error Tracking (Phase 6+)

| | Primary | Alternative 1 | Alternative 2 |
|---|---|---|---|
| **App** | Datadog | New Relic | Azure Monitor |
| **Cost** | Free tier / ~$15/mo | Free tier / ~$25/mo | Included with Azure |
| **Website** | datadoghq.com | newrelic.com | azure.microsoft.com |
| **Why primary** | Best-in-class observability, Cowork MCP available | | |
| **Why alt** | New Relic = generous free tier. Azure Monitor = free if Azure stack | | |
| **Data risk** | ⚠️ Configure to exclude PII from logs — see Section 2 | Same | Same |
| **Company approval** | Widely approved | Widely approved | Best if Azure |

---

### 10. CI/CD (Automated Testing & Deployment)

| | Primary | Alternative 1 | Alternative 2 |
|---|---|---|---|
| **App** | GitHub Actions | GitLab CI/CD | Azure Pipelines |
| **Cost** | Free (2,000 min/mo) | Free | Free with Azure DevOps |
| **Website** | Built into GitHub | Built into GitLab | Built into Azure DevOps |
| **Why primary** | Integrated with GitHub repo, zero additional setup | | |
| **Why alt** | Matches alternative repo choices | Enterprise-grade, likely pre-approved |
| **Data risk** | None — runs tests only, no report data | None | None |

---

## SECTION 2 — Data Security & Privacy Architecture

### 2.1 Data Classification

| Data Type | Classification | Examples | Where Stored |
|---|---|---|---|
| Report files | **CONFIDENTIAL — NPI** | XML/PDF appraisal reports with borrower info | Cloudflare R2 / AWS S3 / Azure Blob |
| Report metadata | **SENSITIVE** | Subject address, form type, appraiser name | PostgreSQL database |
| QC results | **INTERNAL** | Flag categories, quality scores (no PII) | PostgreSQL database |
| Revision messages | **SENSITIVE** | May reference property/borrower details | PostgreSQL database |
| Audit logs | **INTERNAL** | Who accessed what, when | PostgreSQL + log service |
| Application code | **INTERNAL** | No PII ever in code | GitHub |

---

### 2.2 Encryption Requirements

**In Transit (data moving between systems):**
- All API endpoints: HTTPS/TLS 1.2 minimum — enforced by Railway/Azure/Render automatically
- File uploads: HTTPS only — enforced at the API layer
- Database connections: SSL required — configured in DATABASE_URL (`?sslmode=require`)
- Internal service calls: HTTPS only

**At Rest (data sitting in storage):**
- File storage (R2/S3/Azure Blob): AES-256 encryption — enabled by default on all three options
- Database: Enable encryption at rest in Railway/Supabase/Azure settings
- Application logs: Ensure log storage (Datadog/Azure Monitor) has encryption at rest enabled

---

### 2.3 AI API — PII Scrubbing Architecture

**Problem:** The narrative quality scorer sends appraisal text to an external AI API. Raw appraisal text contains borrower names, property addresses, and financial details.

**Solution — Two-Layer Approach:**

**Layer 1: Send only extracted non-PII fields**
The quality scorer never sends raw report text to the AI API. It sends only the structural analysis fields:
```
SEND:    "Neighborhood trend: Stable. Supply/demand: In Balance. Marketing time: 3-6 months."
DON'T SEND: "The subject property at 123 Main St, owned by John Smith..."
```

**Layer 2: PII Scrubber (pre-AI processing)**
File: `backend/app/services/privacy/pii_scrubber.py`

Before any text goes to the AI API, it passes through a scrubber that:
- Replaces proper names with `[PERSON]`
- Replaces addresses with `[ADDRESS]`  
- Replaces SSNs, loan numbers with `[REDACTED]`
- Replaces dollar amounts with `[VALUE]` (preserves relative comparisons)

This means even if a narrative section accidentally contains PII, it is stripped before leaving the system.

**Layer 3: Data Processing Agreement**
Before production launch, execute a DPA with your AI provider:
- Anthropic DPA: https://www.anthropic.com/legal/data-processing-addendum
- Azure OpenAI: included in Microsoft Enterprise Agreement
- AWS Bedrock: included in AWS Business Associate Agreement framework

---

### 2.4 Access Controls

**Authentication:**
- JWT tokens expire after 8 hours (not 24) for production — shorter window limits exposure if token is compromised
- Tokens stored in memory only (not localStorage) to prevent XSS theft
- Password requirements: minimum 12 characters, complexity enforced

**Role-Based Access:**

| Role | Can access report files | Can see borrower PII | Can export data |
|---|---|---|---|
| `appraiser` | Own reports only | Own reports only | No |
| `reviewer` | All reports | Yes | QC results only (no PII) |
| `admin` | All reports | Yes | All (logged) |
| API (Bubble integration) | Assigned orders only | No | Status only |

**File Access:**
- Report files in R2/S3 never publicly accessible — always served via signed URLs
- Signed URLs expire after 15 minutes (not persistent links)
- Signed URL generation logged in audit trail

---

### 2.5 Audit Logging

Every access to NPI data must be logged for GLBA compliance. Log entries include:

```
{
  "timestamp": "2026-06-25T14:32:00Z",
  "user_id": "usr_123",
  "user_role": "reviewer",
  "action": "view_report",
  "report_id": "rpt_456",
  "ip_address": "192.168.1.1",
  "result": "success"
}
```

**Events to log:**
- Report upload
- Report file download / view
- QC result access
- Revision request created/viewed
- User login / logout / failed login
- Admin actions (user creation, rule changes)
- Any data export

**Log retention:** Minimum 3 years (GLBA requirement). Store in separate append-only log storage — not the main database.

---

### 2.6 Data Retention & Deletion

**Retention policy to implement:**

| Data | Retention Period | Action at Expiry |
|---|---|---|
| Report files (XML/PDF) | 7 years from report date | Secure delete from R2/S3 |
| Report metadata | 7 years | Archive then delete |
| QC results & flags | 7 years | Archive then delete |
| Audit logs | 3 years minimum | Archive |
| User accounts | Duration of employment + 1 year | Deactivate then delete |

**Right to deletion:** If a lender requests deletion of a specific report, the system must be able to delete:
1. The file from R2/S3
2. The database records
3. Any cached versions
And log that deletion was performed.

---

### 2.7 Network Security

**Production requirements:**
- API rate limiting: 100 requests/minute per user (prevents bulk data extraction)
- IP allowlisting for admin endpoints (optional but recommended)
- CORS restricted to True Footage domains only — no wildcard `*` origins
- File upload size limit: 50MB (prevents abuse)
- File type validation server-side (not just frontend) — reject anything that isn't XML or PDF

**Secrets management:**
- All credentials in environment variables — never in code
- Rotate API keys quarterly
- Railway/Azure secret management for production — not plain text .env files in production

---

### 2.8 Incident Response Plan

If a data breach occurs:

1. **Immediately:** Revoke all API keys and rotate secrets
2. **Within 24 hours:** Identify what data was accessed and by whom (use audit logs)
3. **Within 72 hours:** GLBA requires notification to your primary federal regulator
4. **Notify affected individuals** if NPI was exposed — GLBA requirement
5. **Document** the incident, response, and corrective actions

Assign an internal point of contact now (before breach) who owns this process.

---

### 2.9 Compliance Checklist (Pre-Production)

- [ ] Data Processing Agreement signed with AI provider (Anthropic/Azure/AWS)
- [ ] Privacy Policy updated to include QC tool data practices
- [ ] Encryption at rest enabled on database
- [ ] Encryption at rest enabled on file storage
- [ ] All API endpoints HTTPS only
- [ ] Signed URL expiry set to 15 minutes
- [ ] Audit logging active and tested
- [ ] PII scrubber tested with sample report
- [ ] Access control testing: appraiser cannot access another appraiser's reports
- [ ] GLBA safeguards rule review with company legal/compliance team
- [ ] Incident response contact assigned
- [ ] Data retention policy documented and scheduled

---

### 2.10 USPAP Confidentiality Compliance

USPAP Ethics Rule requires appraisers to keep assignment results and assignment information confidential. This system must enforce:

- **No report data shared with unauthorized parties** — role-based access controls handle this
- **No appraisal results used for purposes other than QC** — scope limited to QC workflow only
- **Confidential information not disclosed in AI training** — ensure AI provider's DPA includes a "no training on customer data" clause (Anthropic, Azure OpenAI, and AWS Bedrock all provide this)
- **Audit trail** of who accessed what — covered by Section 2.5

---

## SECTION 3 — Recommended Stack by Company Environment

| Your Company Environment | Recommended Stack |
|---|---|
| **Startup / No IT policy yet** | Railway + Cloudflare R2 + Anthropic API + GitHub + Resend |
| **Microsoft 365 shop** | Azure App Service + Azure Blob + Azure OpenAI + Azure DevOps + SendGrid |
| **AWS shop** | AWS Elastic Beanstalk + S3 + AWS Bedrock (Claude) + GitHub Actions + AWS SES |
| **Strict enterprise / regulated** | Azure everything + Azure OpenAI + Jira + SendGrid — get DPAs signed before launch |

---

*App Stack & Security Guide v1.0 — 2026-06-25*  
*Review with True Footage legal/compliance before production launch.*
