# TF AI-QC — Development Tools, Stack & AI Options

**Purpose:** Reference guide for developers and decision-makers. Covers all tools, providers, and AI options for building TF AI-QC to work on either hosting path.

---

## Architecture That Works Either Way

The application is built in layers. The business logic (rules engine, scoring, workflow) is the same regardless of hosting. Only the infrastructure layer changes between internal (GCP) and external (Railway) deployments.

```
[ Appraisers / Reviewers ]
        ↓
[ Web Application — React + TypeScript ]
        ↓
[ API Layer — Python / FastAPI ]
        ↓
[ Rules Engine ] ← [ GSE Compliance API ] ← Fannie Mae / Freddie Mac
        ↓
[ AI Quality Analysis ] ← [ PII Scrubber ] (mandatory before AI)
        ↓
[ Database — PostgreSQL ] + [ File Storage ]
        ↓
[ Auth + Infrastructure ] ← GCP (Option A) or Railway (Option B)
```

---

## Backend

### Python / FastAPI
The server-side application that handles all business logic — receiving reports, running rules, calling AI, managing workflow.

**Key libraries:**
- `fastapi` — web framework
- `sqlalchemy` — database ORM
- `pydantic` — data validation and schema enforcement
- `python-multipart` — file upload handling
- `lxml` or `xmltodict` — UAD 3.6 XML parsing
- `celery` — background task processing (running rule checks async)

---

## Frontend

### React + TypeScript + Tailwind CSS

**Key libraries:**
- `react-query` — data fetching and caching
- `react-hook-form` — form handling
- `shadcn/ui` — pre-built accessible UI components (tables, modals, cards)
- `recharts` or `chart.js` — performance dashboard charts
- `react-pdf` — PDF rendering in-browser for report viewing

---

## Database

### PostgreSQL
Works identically on both hosting paths.

- **Option A (GCP):** Cloud SQL for PostgreSQL — fully managed, automated backups, IAM-integrated access
- **Option B (External):** Railway managed PostgreSQL or Neon (serverless PostgreSQL)

---

## File Storage

- **Option A (GCP):** Google Cloud Storage — integrates natively with Cloud DLP for PII scanning
- **Option B (External):** Cloudflare R2 — S3-compatible API, no egress fees, SOC 2 certified

---

## Authentication

- **Option A (GCP):** Firebase Authentication with Google SSO — single sign-on using existing True Footage Google Workspace accounts
- **Option B (External):** Auth0 or Clerk — managed authentication with SSO support

---

## AI Options for Quality Analysis

A PII scrubber must run before any appraisal text reaches an AI service.

### Tier 1 — Fully Internal (NPI Never Leaves Company Control)

**Vertex AI (Google Cloud)**
- Processes data within the company's GCP tenant
- Google Cloud DPA covers AI processing — no separate agreement needed
- Models: Gemini 1.5 Pro/Flash
- Best fit for Option A (GCP)
- FedRAMP Moderate authorized

**Self-Hosted LLM via Ollama or vLLM**
- Model runs on company hardware or a private VM — data never leaves the server
- No vendor agreement required — open source
- Recommended models: Llama 3.3 70B, Qwen 2.5 72B (both perform comparably to GPT-4o on document analysis)
- **Ollama:** Best for development and pilot — minimal setup, runs quickly
- **vLLM:** Best for production — up to 10x higher throughput than Ollama
- Hardware requirement: ~43GB VRAM for Llama 70B at quantized precision

### Tier 2 — Cloud AI with Strong Data Agreements

**Azure OpenAI Service**
- Clearest enterprise DPA — data not used for training by default
- FedRAMP High authorized
- Models: GPT-4o, GPT-4o-mini with enterprise controls
- VPC endpoint support — traffic stays inside private network
- Best if company already has Azure enterprise agreement

**AWS Bedrock**
- FedRAMP High authorized
- VPC endpoint support
- Models: Claude 3.5 Sonnet/Haiku, Llama 3.3, Amazon Titan
- Best if company already uses AWS

**Anthropic Claude API (Direct)**
- Most capable models for document analysis (Claude Opus, Sonnet)
- Enterprise DPA required before NPI use
- No VPC endpoint — encrypted public internet traffic
- Best fit for Option B (external hosting) after DPA is executed

---

## PII Scrubbing (Mandatory Before Any AI Call)

**Google Cloud DLP API (Recommended for Option A)**
- Pre-built detectors for names, addresses, SSNs, phone numbers, financial data
- Native GCP integration
- Cost: ~$1–3 per 1,000 report pages

**Microsoft Presidio (Open Source — Option B)**
- Runs locally — no data leaves server
- Free, self-hosted
- GitHub: github.com/microsoft/presidio

---

## Rules Engine

### Layer 1 — GSE Hard Rules (Use the API, Do Not Rebuild)

**Fannie Mae UAD Compliance API**
- 709 URAR rules + 102 Restricted Report rules — already built and maintained by Fannie Mae
- Updated May 14, 2026 — stays current automatically
- Free — requires registration with Fannie Mae
- Register: singlefamily.fanniemae.com/delivering/uniform-mortgage-data-program/uniform-appraisal-dataset

**Freddie Mac UAD Compliance API**
- Parallel validation for Freddie Mac overlays
- Free — requires Freddie Mac seller/servicer registration

### Layer 2 — Internal Quality Rules (Build These)

**Zen Engine (Recommended)**
- Open-source Python/Rust rules engine — sub-millisecond evaluation
- Supports decision tables — rules can be written in spreadsheet format (non-developer friendly)
- Rules stored as JSON/YAML — auditable, version-controlled
- GitHub: github.com/gorules/zen

**rule-engine (Python)**
- Lightweight Python library for matching rules against data objects
- PyPI: pypi.org/project/rule-engine

**Decision Tables (Excel / CSV)**
- Kevin defines rules in a spreadsheet; engine evaluates them
- Non-technical rule authoring — QDS can add/modify rules without developer help
- Zen Engine natively supports this format

### Layer 3 — AI Quality Scoring (LLM-Based)

For subjective quality dimensions (narrative quality, market analysis depth, comp selection rationale) that cannot be captured in hard rules, the LLM evaluates the text and produces a scored finding with reasoning.

---

## Development Environment & Tooling

| Tool | Purpose |
|------|---------|
| VSCode + Claude Code extension | Primary development environment with AI assistance |
| GitHub (private repos) | Source control |
| GitHub Actions | CI/CD — automated test and deploy on push |
| Docker | Local environment consistency |
| REST Client (VSCode) | API testing |
| pgAdmin or TablePlus | Database inspection |

---

## Claude Code Skills & Plugins Relevant to This Build

| Skill / Plugin | Use |
|---------------|-----|
| `/research` (knowledge-worker) | Research UAD rule specifics, GSE guidelines before implementing |
| `/appraisal-summary` (knowledge-worker) | Validate AI output against your own review of the same report |
| `serena` (marketplace) | AI-powered code search as codebase grows |
| `playwright` (marketplace) | Automated browser testing of reviewer and appraiser UIs |
| `context7` (marketplace) | Live documentation for FastAPI, React, SQLAlchemy pulled into Claude context |

---

## Sources

- [Best self-hosted AI models for regulated industries](https://predictionguard.com/blog/best-self-hosted-ai-models-regulated-industries)
- [Ollama vs vLLM: Local vs Production LLM Inference (2026)](https://www.spheron.network/blog/ollama-vs-vllm/)
- [AWS Bedrock vs Azure OpenAI vs Google Vertex AI Enterprise Comparison](https://www.agilesoftlabs.com/blog/2026/05/aws-bedrock-vs-azure-openai-vs-google)
- [Fannie Mae UAD Compliance API Rules](https://singlefamily.fanniemae.com/media/document/pdf/appraisal-update-report-uad-36-compliance-rules)
- [Zen Engine Python Rules Engine](https://gorules.io/open-source/python-rules-engine)
- [Top Python Rule Engines 2026](https://www.nected.ai/blog/python-rule-engines-automate-and-enforce-with-python)
- [Private LLM Deployment Guide 2026](https://petronellatech.com/blog/private-ai-deployment-guide-enterprise/)
