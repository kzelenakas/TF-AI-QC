# TF AI-QC: IT & Legal Hosting Decision Brief

**Prepared by:** Kevin Zelenakas, Quality Development Specialist — True Footage
**Date:** June 27, 2026
**Purpose:** IT and legal sign-off on hosting architecture for internal appraisal quality control platform

---

## What This Tool Is

TF AI-QC is an internal software tool that automates the review of residential appraisal reports. Appraisers submit UAD 3.6 reports; the system runs compliance checks against GSE and USPAP standards, scores report quality, manages the revision request workflow, and tracks appraiser performance over time.

This tool processes **non-public personal information (NPI)** as defined under GLBA — including borrower names, property addresses, and loan-level data embedded in appraisal reports. All architecture decisions must account for this.

---

## The Decision

Two hosting paths are under evaluation. IT and legal sign-off is required before development proceeds on either.

---

## Option A — Internal (Google Workspace / GCP)

**Architecture:** Google Cloud Platform — Cloud Run (application), Cloud SQL/PostgreSQL (database), Google Cloud Storage (file storage), Vertex AI (AI processing), Firebase or Google Identity (authentication), Google Cloud DLP API (PII scrubbing before AI)

**Data flow:**
1. Appraiser uploads report → Google Cloud Storage (inside company GCP tenant)
2. Cloud DLP API scrubs PII from report text before any AI processing
3. Scrubbed text sent to Vertex AI for quality analysis
4. Results stored in Cloud SQL
5. Reviewer accesses results via internal web application
6. NPI never leaves the company's GCP environment

**Compliance posture:**
- Data stays within company-controlled GCP tenant at all times
- Google Cloud has SOC 2 Type II, ISO 27001, and supports GLBA compliance programs
- Google Cloud DLP provides automated PII detection and redaction
- Access controls managed via Google Identity (same as existing Google Workspace accounts)
- No third-party AI vendor receives NPI — Vertex AI processes are within the same GCP account

**What IT needs to approve:**
- GCP project creation and billing setup
- Network/firewall rules for internal access
- Service account permissions and IAM roles
- Integration with existing Google Workspace SSO

**What legal needs to sign off:**
- Google Cloud data processing agreement (DPA) — already standard with Google Workspace Enterprise
- Confirm GCP tenant data residency settings meet GLBA requirements
- Confirm Vertex AI usage within existing GCP DPA scope

**Estimated infrastructure cost:** $200–$600/month at current team size (Cloud Run, Cloud SQL, Cloud Storage, Vertex AI token usage)

---

## Option B — External (Railway / Cloudflare / Anthropic Claude API)

**Architecture:** Railway (application + database hosting), Cloudflare R2 (file storage), Anthropic Claude API (AI processing), custom PII scrubber (mandatory before any text reaches Claude API)

**Data flow:**
1. Appraiser uploads report → Cloudflare R2 (outside company network)
2. Custom PII scrubber removes NPI from report text
3. Scrubbed text sent to Anthropic Claude API for quality analysis
4. Results stored in Railway PostgreSQL
5. Reviewer accesses results via web application hosted on Railway
6. NPI must be fully removed before leaving company control — scrubber is a critical dependency

**Compliance posture:**
- Data transits and is stored on third-party infrastructure (Railway, Cloudflare)
- Anthropic offers a data processing agreement (DPA) for enterprise accounts — required before use
- PII scrubber effectiveness is a compliance dependency — a gap in scrubbing = NPI exposure
- Railway and Cloudflare have SOC 2 certifications but are not purpose-built for GLBA regulated industries
- FTC Safeguards Rule requires written contracts with all service providers who access NPI

**What IT needs to approve:**
- Network policy for outbound traffic to Railway, Cloudflare, Anthropic
- Security review of third-party vendors (Railway, Cloudflare, Anthropic)
- Approval of PII scrubber architecture and testing methodology

**What legal needs to sign off:**
- Data Processing Agreement with Anthropic (enterprise required)
- Vendor assessment for Railway and Cloudflare under GLBA Safeguards Rule §314.4(f)
- Written contracts with each third-party service provider confirming NPI protections
- PII scrubber validation — legal must confirm scrubbing standard meets GLBA requirements

**Estimated infrastructure cost:** $100–$300/month at current team size, plus Claude API token costs (variable by usage)

---

## Side-by-Side Summary

| | Option A (Internal / GCP) | Option B (External / Railway) |
|--|--------------------------|-------------------------------|
| **NPI leaves company control?** | No | Only if scrubber fails |
| **Approval complexity** | Lower — GCP DPA likely exists | Higher — 3 new vendor agreements |
| **Compliance risk** | Lower | Higher (scrubber dependency) |
| **Build complexity** | Moderate | Lower |
| **IT involvement** | GCP setup + IAM | Outbound network policy only |
| **Monthly cost** | $200–$600 | $100–$300 + API usage |
| **Timeline to approval** | Faster (Google relationship exists) | Slower (new vendor vetting) |

---

## Recommendation

**Option A (Internal / GCP) is recommended** for compliance simplicity. NPI stays inside the company's existing GCP environment, the Google DPA is likely already in place under the company's Google Workspace agreement, and the approval path is shorter.

Option B remains viable if GCP is not available or preferred, but requires three separate vendor agreements and a validated PII scrubber architecture before any live appraisal data is used.

---

## Approvals Required

| Approver | Option A | Option B |
|----------|---------|---------|
| **IT** | GCP project + IAM approval | Outbound network + vendor security review |
| **Legal** | Confirm GCP DPA covers Vertex AI | DPAs with Anthropic, Railway, Cloudflare + scrubber validation |
| **Management** | Budget approval ($200–$600/mo) | Budget approval ($100–$300/mo + API costs) |

---

## Questions for This Review

1. Does the company's existing Google Workspace / GCP agreement include a GLBA-compliant data processing agreement that covers Vertex AI?
2. Has IT evaluated Railway and Cloudflare as approved vendors?
3. Is there a preferred cloud provider already approved for NPI workloads?
4. What is the required timeline for legal vendor review?

---

*Contact: Kevin Zelenakas — kzelenakas@gmail.com*
