# TF AI-QC Deployment Checklist

## Pre-Deploy

- [ ] Supabase project created; connection string available
- [ ] Cloudflare R2 bucket `tf-ai-qc-reports` created with public access **OFF**
- [ ] R2 API token generated (read + write on bucket)
- [ ] Resend account verified; sending domain configured
- [ ] Bubble app has API Connector plugin installed
- [ ] Bubble JWT signing secret documented
- [ ] Railway project created; GitHub repo connected to `main` branch
- [ ] Ollama service deployed on Railway with `glm-4.7-flash` pulled

## Railway Environment Variables

Copy all values from `backend/.env.production.template` into Railway service variables.

Required secrets:
- `DATABASE_URL` — Supabase connection string
- `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`
- `BUBBLE_AUTH_SECRET` — must match Bubble JWT signing config
- `INTERNAL_CRON_SECRET` — for `/internal/*` endpoints
- `RESEND_API_KEY`

## First Deploy

1. Push to `main` → Railway auto-deploys
2. Railway runs: `alembic upgrade head` then `python -m app.cli seed-rules`
3. Verify health: `curl https://your-service.railway.app/health`
4. Create first admin: `railway run python -m app.cli create-admin --email admin@truefootage.com --bubble-id <bubble_id>`
5. Verify rules seeded: `railway run python -m app.cli list-rules`

## Post-Deploy Verification

- [ ] `GET /health` → `{"status": "ok"}`
- [ ] `POST /internal/health-check` with `X-Internal-Secret` header → all green
- [ ] Upload a synthetic UAD XML report → status progresses to `qc_complete`
- [ ] Approve report → Bubble OMS sync fires; appraiser email sent
- [ ] Admin can disable/enable a rule via `PATCH /rules/{code}/disable`
- [ ] Coaching profile loads for a test appraiser

## Railway Cron Setup

In Railway dashboard, add a cron job:
- **Schedule**: `*/30 * * * *` (every 30 min)
- **Command**: `curl -X POST $RAILWAY_PUBLIC_DOMAIN/internal/retry-stuck-reports -H "X-Internal-Secret: $INTERNAL_CRON_SECRET"`

And a daily health check:
- **Schedule**: `0 8 * * *` (8am daily)
- **Command**: `curl -X POST $RAILWAY_PUBLIC_DOMAIN/internal/health-check -H "X-Internal-Secret: $INTERNAL_CRON_SECRET"`

## Supabase Checklist

- [ ] Connection pooler enabled (PgBouncer in transaction mode)
- [ ] Row Level Security disabled on all tables (access controlled at API layer)
- [ ] Point-in-time recovery enabled (PITR) — required for 3-year audit log retention
- [ ] `audit` log table backed up separately if using Supabase logging
