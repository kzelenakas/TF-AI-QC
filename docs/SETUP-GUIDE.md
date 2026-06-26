# TF AI-QC — Complete Setup Guide
**Complete this entire guide before running Session 0.**  
Estimated time: 2–3 hours total (mostly waiting for verifications)

---

## Overview: What You're Setting Up

| Service | Purpose | Cost |
|---|---|---|
| GitHub | Code repository | Free |
| Railway | App hosting + PostgreSQL database | ~$5–20/mo |
| Cloudflare | File storage (R2) for appraisal reports | Free for beta |
| Anthropic API | Claude AI for quality scoring | Pay per use (~$50–100/mo) |
| Resend | Email notifications | Free up to 3,000/mo |
| Node.js | Run React frontend locally | Free |
| Python | Run FastAPI backend locally | Free |
| VS Code | Code editor | Free |

---

## STEP 1 — GitHub (Already Done ✓)

You have: `github.com/kzelenakas/TF-AI-QC`

**Still needed:**
1. Go to https://github.com/settings/tokens/new (classic token page)
2. Note: **Name:** `TF-AI-QC Dev`, **Expiration:** 90 days, **Scope:** check `repo` only
3. Click **Generate token** → copy and save it somewhere safe (password manager)
4. You'll use this token as your git password for all future pushes

---

## STEP 2 — Python

**Check if you already have it:**
Open PowerShell and run:
```powershell
python --version
```
If it shows Python 3.11 or higher, skip to Step 3.

**Install Python:**
1. Go to https://www.python.org/downloads/
2. Download the latest Python 3.12.x Windows installer
3. Run the installer — **IMPORTANT: check "Add Python to PATH"** before clicking Install
4. Verify: open a new PowerShell window and run `python --version`

---

## STEP 3 — Node.js

**Check if you already have it:**
```powershell
node --version
npm --version
```
If both show version numbers (Node 18+ preferred), skip to Step 4.

**Install Node.js:**
1. Go to https://nodejs.org/
2. Download the **LTS** version (left button)
3. Run the installer with all defaults
4. Verify: open a new PowerShell window and run `node --version`

---

## STEP 4 — VS Code (Code Editor)

1. Go to https://code.visualstudio.com/
2. Click **Download for Windows**
3. Run the installer with all defaults
4. Open VS Code after install

**Install these VS Code extensions** (open VS Code → click Extensions icon on left sidebar → search each name):
- `Python` (by Microsoft)
- `Pylance` (by Microsoft)
- `ES7+ React/Redux/React-Native snippets`
- `Tailwind CSS IntelliSense`
- `GitLens`
- `REST Client` (for testing API endpoints)

---

## STEP 5 — Railway (App Hosting + Database)

Railway hosts your backend and provides a managed PostgreSQL database.

1. Go to https://railway.app/
2. Click **Login** → **Login with GitHub** (use your GitHub account)
3. Authorize Railway to access GitHub
4. Once logged in, click **New Project**
5. Select **Empty Project** — name it `TF-AI-QC`
6. Click **Add a Service** → **Database** → **PostgreSQL**
   - Railway creates a Postgres database automatically
   - Click the database tile → **Connect** tab → copy the `DATABASE_URL` — save it
7. Go to **Account Settings** → **Billing** → add a credit card
   - Railway's free tier is limited; the Starter plan (~$5/mo) is enough for beta
8. Install the Railway CLI (for deploying from terminal):
   ```powershell
   npm install -g @railway/cli
   railway login
   ```
   Follow the browser prompt to authenticate.

---

## STEP 6 — Cloudflare (File Storage)

Cloudflare R2 stores the uploaded XML and PDF appraisal report files.

1. Go to https://dash.cloudflare.com/sign-up
2. Create an account with your email — verify your email address
3. Once logged in, click **R2 Object Storage** in the left sidebar
   - If you don't see it: click **+ Add** and enable R2
4. Click **Create bucket**
   - **Bucket name:** `tf-ai-qc-reports`
   - **Location:** Automatic
   - Click **Create bucket**
5. Get your API credentials:
   - Click **Manage R2 API Tokens**
   - Click **Create API Token**
   - **Permissions:** Object Read & Write
   - **Specify bucket:** `tf-ai-qc-reports`
   - Click **Create API Token**
   - Copy and save:
     - `Access Key ID`
     - `Secret Access Key`
     - `Endpoint URL` (looks like `https://[account-id].r2.cloudflarestorage.com`)

---

## STEP 7 — Anthropic API (Claude AI)

The rule engine uses Claude to score narrative quality in appraisal reports.

1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Click **API Keys** in the left sidebar
4. Click **Create Key** → name it `TF-AI-QC`
5. Copy the key immediately — you won't see it again
6. Click **Billing** → add a credit card
   - Recommended: set a usage limit of $100/month to start
   - Claude API pricing: roughly $0.003 per 1,000 tokens (narrative scoring uses ~500 tokens per report section)

---

## STEP 8 — Resend (Email Notifications)

Resend sends emails when revisions are requested or reports are approved.

1. Go to https://resend.com/
2. Click **Sign Up** → create account
3. Verify your email address
4. Click **API Keys** → **Create API Key** → name it `TF-AI-QC`
5. Copy the API key
6. Click **Domains** → **Add Domain**
   - Use `truefootage.com` or whatever domain True Footage owns
   - Follow the DNS verification steps (add the DNS records they show you to your domain registrar)
   - If you don't have a domain yet, Resend's free sandbox mode works for beta testing

---

## STEP 9 — Save All Your Credentials

Create this file on your computer (NOT in the project folder — keep it in a safe place like a password manager):

```
TF AI-QC Credentials

GitHub Token: ghp_xxxxxxxxxxxx
Railway DATABASE_URL: postgresql://...
Cloudflare R2 Endpoint: https://[id].r2.cloudflarestorage.com
Cloudflare R2 Bucket: tf-ai-qc-reports
Cloudflare R2 Access Key ID: xxxxxxxxxxxx
Cloudflare R2 Secret Access Key: xxxxxxxxxxxx
Anthropic API Key: sk-ant-xxxxxxxxxxxx
Resend API Key: re_xxxxxxxxxxxx
```

You'll paste these into Railway's environment variables dashboard in Session 6 (deployment).

---

## STEP 10 — Open Your Project in VS Code

1. Open VS Code
2. Click **File** → **Open Folder**
3. Navigate to `C:\Users\kzele\Claude Cowork\Projects\TF AI-QC`
4. Click **Select Folder**
5. You should see the full project structure in the left sidebar

This is your working environment for reviewing code that Claude writes during each session.

---

## STEP 11 — Connect GitHub MCP in Cowork

This lets Claude commit and push code directly without you using the terminal.

1. Open Cowork
2. Click the **Connectors** or **Plugins** icon
3. Search for **GitHub**
4. Click **Connect** → authenticate with your GitHub account
5. Grant access to the `TF-AI-QC` repository

---

## STEP 12 — Connect Cloudflare MCP in Cowork (Optional but Recommended)

Lets Claude manage R2 storage buckets directly.

1. In Cowork Connectors, search for **Cloudflare**
2. Click **Cloudflare Developer Platform** → **Connect**
3. Authenticate with your Cloudflare account

---

## STEP 13 — Install Linear for Project Tracking (Optional)

Linear is better than a text file for tracking what's been built, what's broken, and what's next across 20 sessions.

1. Go to https://linear.app/
2. Sign up → **Create a workspace** → name it `True Footage`
3. Create a project: **TF AI-QC**
4. In Cowork Connectors, search **Linear** → Connect → authenticate

---

## STEP 14 — Add Context Documents to Project

Before running Session 0, drop these reference docs into your project folder:

**Where to get them:**

| Document | Where to find it |
|---|---|
| USPAP current edition | appraisalfoundation.org → Publications → USPAP |
| UAD Appendix D (field definitions) | fanniemae.com → search "UAD Appendix D" |
| Fannie Mae Selling Guide B4-1 | selling-guide.fanniemae.com → B4-1 (Appraisals) |
| FHA 4000.1 Handbook Ch. II.D | hud.gov → search "4000.1 handbook" → Chapter II.D |
| VA Lender Handbook Ch. 11 | benefits.va.gov → search "VA Lender Handbook Chapter 11" |
| New URAR sample (redacted) | Export from your appraisal software or ask a staff appraiser |

**Where to put them:**

```
context/
├── guidelines/
│   ├── uspap/         ← USPAP current edition PDF
│   └── gse/           ← Fannie Mae B4-1, FHA 4000.1, VA Ch.11 PDFs
├── rule-references/
│   └── uad-3.6/       ← UAD Appendix D PDF
└── sample-reports/
    └── 1004/          ← Redacted new URAR sample (PDF + XML if available)
```

⚠️ Remove all borrower names, SSNs, and loan numbers from any sample reports before adding them.

---

## STEP 15 — Verify Everything

Run this checklist before starting Session 0:

- [ ] GitHub repo accessible at github.com/kzelenakas/TF-AI-QC
- [ ] GitHub classic PAT token saved
- [ ] Python 3.11+ installed (`python --version`)
- [ ] Node.js 18+ installed (`node --version`)
- [ ] VS Code installed with extensions
- [ ] Railway account created, PostgreSQL added, DATABASE_URL saved
- [ ] Cloudflare R2 bucket created, credentials saved
- [ ] Anthropic API key saved
- [ ] Resend API key saved
- [ ] All credentials stored safely (not in project folder)
- [ ] At least one reference doc in context/ folder
- [ ] Project folder open in VS Code

---

## You're Ready — Start Session 0

1. Open Cowork
2. Switch model to **claude-opus-4-8**
3. Make sure **TF AI-QC** project folder is selected
4. Open `prompts/PLAYBOOK.md`
5. Copy the **SESSION 0** prompt and paste it as your first message

---

*Setup Guide v1.0 — 2026-06-25*
