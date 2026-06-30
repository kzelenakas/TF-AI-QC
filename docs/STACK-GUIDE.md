# TF AI-QC — Stack Guide (v3.0)
**Date:** 2026-06-29
**Replaces:** GOOGLE-CLOUD-GUIDE.md (GCP stack), PLAYBOOK.md (Railway v1)

---

## Decision Summary

True Footage already runs its order management system (OMS) on Bubble.io. This stack aligns the QC tool with that environment — eliminating the React frontend, reducing vendor count, and cutting beta ops cost.

| Component | Choice | Replaces |
|---|---|---|
| Backend | FastAPI on **Railway** | Cloud Run |
| Database | **Supabase** (PostgreSQL 15) | Cloud SQL |
| File storage | **Cloudflare R2** | Google Cloud Storage |
| Auth | **Bubble native auth** | Firebase Authentication |
| Frontend | **Bubble** (True Footage app) | React + Firebase Hosting |
| AI scoring | **Ollama** (`glm-4.7-flash`) | Vertex AI / Gemini |
| AI fallback | Claude API (if Ollama unreachable) | — |
| Email | **Resend** | SendGrid |
| Background jobs | Railway cron + workers | Cloud Tasks |
| CI/CD | Railway auto-deploy (GitHub `main`) | Cloud Build |
| Agent harness | **Ruflo** | — |

---

## Why Each Choice

### Railway (Backend Hosting)
- Deploy on push to `main` — zero config CI/CD
- Managed environment variables (no Secret Manager setup)
- Ollama runs as second Railway service on same project
- ~$5–20/mo at beta volume
- No Docker expertise required for basic deploys

### Supabase (Database)
- PostgreSQL 15 — all complex coaching/analytics queries work unchanged
- Native Bubble connector available in Bubble marketplace
- REST API — Bubble can query it directly when needed
- SOC 2 Type II, GLBA-ready DPA
- Free tier: 500MB DB, 2 projects — covers beta

### Cloudflare R2 (File Storage)
- Zero egress fees (critical — appraisal XML/PDF files read frequently)
- S3-compatible API — standard Python `boto3` client works
- AES-256 encryption at rest by default
- SOC 2 Type II

### Bubble (Frontend)
- True Footage already builds and maintains Bubble — no new platform
- QC tool pages live inside the existing Bubble app
- Bubble's API Connector plugin calls FastAPI backend
- Eliminates 4 React build sessions (Sessions 5A/5B/5C/5D)
- Native OMS data access — no separate integration layer needed

### Ollama + glm-4.7-flash (AI)
- Runs on Railway as a service — data never leaves infrastructure
- No DPA required (NPI stays internal)
- No per-token cost
- OpenAI-compatible API — backend uses standard `openai` Python SDK pointed at Ollama endpoint
- Fallback: if Ollama service unreachable, `ai/ollama_client.py` falls back to Claude API
- Trade-off: smaller model — narrative quality scoring may be less precise than Gemini 2.5 Pro; acceptable for beta

### Bubble Auth
- Appraisers already have Bubble accounts via OMS
- Bubble generates JWT-style tokens on login
- Backend verifies token on every request, extracts `user_id` + `role`
- No separate auth system to manage

---

## Cost Estimate (Beta)

| Service | Est. Monthly |
|---|---|
| Railway (backend + Ollama) | ~$10–25 |
| Supabase | Free tier |
| Cloudflare R2 | ~$0–5 |
| Resend | Free tier (<3k emails/mo) |
| Claude API fallback | ~$0–20 (only fires if Ollama down) |
| **Total** | **~$10–50/mo** |

Set Railway spend limit to $75/mo as a guardrail.

---

## Environment Variables (Railway)

```
# Database
DATABASE_URL=postgresql://...supabase...

# Cloudflare R2
R2_ACCOUNT_ID=
R2_ACCESS_KEY_ID=
R2_SECRET_ACCESS_KEY=
R2_BUCKET_NAME=tf-ai-qc-reports

# Ollama
OLLAMA_BASE_URL=http://ollama:11434/v1
OLLAMA_MODEL=glm-4.7-flash

# Claude API (fallback)
ANTHROPIC_API_KEY=

# Bubble
BUBBLE_APP_NAME=
BUBBLE_API_TOKEN=
BUBBLE_AUTH_SECRET=

# Resend
RESEND_API_KEY=

# App
SECRET_KEY=
ENVIRONMENT=production
CORS_ORIGINS=https://your-bubble-app.bubbleapps.io
```

All set in Railway dashboard → Service → Variables. Never committed to repo.

---

## Ollama Setup

### Local Dev
```powershell
# Install Ollama (Windows)
# Download from https://ollama.com

# Pull model
ollama pull glm-4.7-flash

# Start server (runs on localhost:11434)
ollama serve
```

### Production (Railway)
Deploy Ollama as a second Railway service:
1. New service → Docker image: `ollama/ollama`
2. Add volume for model storage
3. Add start command: `ollama serve`
4. Pull model on first boot via Railway start script:
   ```bash
   ollama pull glm-4.7-flash && ollama serve
   ```
5. Backend service sets `OLLAMA_BASE_URL=http://ollama:11434/v1` (Railway internal networking)

### Backend Client (`backend/app/services/ai/ollama_client.py`)
```python
from openai import AsyncOpenAI

ollama = AsyncOpenAI(
    base_url=settings.OLLAMA_BASE_URL,
    api_key="ollama"
)

async def score_narrative(text: str) -> dict:
    try:
        response = await ollama.chat.completions.create(
            model=settings.OLLAMA_MODEL,
            messages=[{"role": "user", "content": text}]
        )
        return parse_score_response(response)
    except Exception:
        # Fallback to Claude API
        return await score_narrative_claude(text)
```

---

## Supabase Setup

1. Create project at supabase.com
2. Copy connection string (Transaction pooler, port 6543)
3. Set `DATABASE_URL` in Railway
4. Run migrations: `alembic upgrade head`
5. In Bubble: install Supabase connector from marketplace → paste project URL + anon key

**Bubble reads QC results directly from Supabase** for display — no backend hop needed for read-only dashboard data.

---

## Cloudflare R2 Setup

1. Cloudflare dashboard → R2 → Create bucket: `tf-ai-qc-reports`
2. R2 → Manage API Tokens → Create token (Object Read & Write)
3. Copy Account ID, Access Key ID, Secret Access Key
4. Set in Railway environment variables
5. Backend uses `boto3` with custom endpoint:
```python
import boto3
s3 = boto3.client(
    "s3",
    endpoint_url=f"https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
    aws_access_key_id=settings.R2_ACCESS_KEY_ID,
    aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
)
```

**Public access blocked** — all file access via 15-minute presigned URLs only.

---

## Bubble Integration

### API Connector Setup (in Bubble)
1. Bubble editor → Plugins → API Connector
2. Add API: `TF AI-QC Backend`
3. Base URL: `https://your-railway-service.up.railway.app`
4. Shared headers: `Authorization: Bearer <bubble_token>` (use Bubble's dynamic `Current User token`)

### Key API calls from Bubble
| Bubble Action | Endpoint |
|---|---|
| Upload report | `POST /reports/upload` |
| Get report list | `GET /reports` |
| Get QC results | `GET /reports/:id/results` |
| Submit revision response | `POST /revisions/:id/respond` |
| Approve report | `POST /reports/:id/approve` |
| Get coaching summary | `GET /coaching/appraiser/:id/summary` |

### OMS Sync
`bubble_client.py` pushes QC status back to OMS on every report state change:
- `submitted` → OMS: "QC Submitted"
- `approved` → OMS: "QC Approved"
- `revision_requested` → OMS: "QC Revision Needed"

---

## Build Session Order

Sessions map to the same backend logic as the original spec. Frontend sessions replaced by Bubble build work.

| Session | What gets built |
|---|---|
| 0 | Railway scaffold, Supabase connection, R2 client, Ollama client |
| 1A | Database models (SQLAlchemy) + Alembic migrations |
| 1B | Bubble auth verification middleware |
| 1C | R2 file upload endpoint |
| 2A | UAD 3.6 XML parser |
| 2B | PDF extractor |
| 3A | Rule engine framework + UAD formatting rules |
| 3B | GSE overlay rules (Fannie Mae, Freddie Mac, FHA, VA) |
| 3C | Quality scoring + Ollama narrative scorer + PII scrubber |
| 3D | Rule admin API + full pipeline wiring |
| 4A | Workflow state machine |
| 4B | Revision request system |
| 5 | **Bubble UI** — appraiser portal, reviewer dashboard, admin panel |
| 6 | Deploy to Railway + smoke tests |
| 7A | Pattern detection engine (coaching) |
| 7B | Coaching report export (PDF) |
| 8 | Bubble OMS deep integration + status sync |

---

## Security Checklist (Pre-Production)

- [ ] All API endpoints HTTPS (Railway enforces automatically)
- [ ] Bubble auth token verified on every backend request
- [ ] R2 bucket public access blocked
- [ ] Signed URLs set to 15-minute expiry
- [ ] PII scrubber tested — confirm no names/addresses reach Ollama
- [ ] All credentials in Railway env vars — no `.env` in repo
- [ ] Supabase SSL connections required
- [ ] Audit logging active — all NPI access logged
- [ ] CORS restricted to Bubble domain only
- [ ] Rate limiting: 100 req/min per user
- [ ] Supabase DPA reviewed for GLBA coverage
- [ ] Cloudflare DPA reviewed for GLBA coverage
- [ ] Railway spend limit set ($75/mo)

---

*Stack Guide v3.0 — 2026-06-29*
