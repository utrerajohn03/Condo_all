# Deploying to Vercel + Supabase

This repo is a **split deployment**: two separate Vercel projects (backend
API, frontend static site) pointed at one Supabase Postgres database.

```
condo-argo-assessment/          ← push this whole repo to GitHub first
├── backend/    → Vercel project #1 (root directory: backend)
├── frontend/   → Vercel project #2 (root directory: frontend)
```

Files already added/adjusted for this:
- `backend/api/index.py` + `backend/vercel.json` — Vercel Python serverless entrypoint
- `backend/app/database.py` — uses `NullPool` when `VERCEL` env var is set (serverless-safe)
- `frontend/vercel.json` — SPA rewrite so React Router routes don't 404 on refresh
- `backend/.env.example`, `frontend/.env.production.example` — filled-in templates below

---

## 1. Push to GitHub

```
git init
git add .
git commit -m "Ready for Vercel + Supabase"
git remote add origin <your-repo-url>
git push -u origin main
```

## 2. Create the Supabase project

1. supabase.com → New project. Note the database password you set.
2. Project Settings → Database → **Connection string**. You'll need two variants:
   - **Session/Direct** (port 5432) — used once, locally, to run migrations.
   - **Transaction pooler** (port 6543) — used by the deployed app.

## 3. Run migrations against Supabase (one-time, from your machine)

```bash
cd backend
python3.11 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` — set `DATABASE_URL` to the **direct** (port 5432) Supabase connection string:
```
DATABASE_URL=postgresql+psycopg2://postgres:YOUR_PASSWORD@db.xxxxxxxxxxxx.supabase.co:5432/postgres?sslmode=require
```

Then:
```bash
alembic upgrade head
python -m scripts.seed_db   # optional: seeds demo org/users/units
```

## 4. Deploy the backend to Vercel

New Vercel project → import the GitHub repo → **Root Directory: `backend`**.
Vercel should auto-detect the Python runtime from `backend/vercel.json`.

Environment variables (Project Settings → Environment Variables):
| Key | Value |
|---|---|
| `DATABASE_URL` | The **pooler** (port 6543) connection string this time, e.g. `postgresql+psycopg2://postgres.xxxx:PASSWORD@aws-0-REGION.pooler.supabase.com:6543/postgres?sslmode=require` |
| `JWT_SECRET_KEY` | A long random string (e.g. `openssl rand -hex 32`) |
| `JWT_ALGORITHM` | `HS256` |
| `JWT_EXPIRE_MINUTES` | `240` |
| `CORS_ORIGINS` | Your frontend's Vercel URL, e.g. `https://condo-argo-frontend.vercel.app` (add after step 5, then redeploy) |

Deploy. Confirm `https://your-backend-project.vercel.app/health` returns `{"status": "ok"}`.

## 5. Deploy the frontend to Vercel

New Vercel project → same GitHub repo → **Root Directory: `frontend`**.
Vercel auto-detects Vite (`npm run build`, output `dist`).

Environment variable:
| Key | Value |
|---|---|
| `VITE_API_BASE` | Your backend project's URL from step 4, e.g. `https://your-backend-project.vercel.app` (no trailing slash) |

Deploy. Since `VITE_API_BASE` is baked in at build time, **redeploy the frontend
any time you change it**.

## 6. Close the loop

Go back to the backend project's `CORS_ORIGINS` env var, set it to the frontend's
real URL from step 5, and redeploy the backend. (`*` works for testing but blocks
cookies/credentials in some browsers — tighten it once you have the real URL.)

## 7. Verify

- Open the frontend URL → login page loads.
- Log in with a seeded test account (see main `README.md` → Test Accounts).
- Network tab: requests should go to `https://your-backend-project.vercel.app/api/...`
  and succeed (not CORS-blocked, not 401 on a fresh login).

## Notes / gotchas

- **Cold starts**: Vercel Python functions spin down when idle — first request
  after a while will be slower. Normal for this hosting model.
- **Connection pooling is mandatory**: always use Supabase's port-6543 pooler
  URL for the deployed `DATABASE_URL`, never the direct 5432 one — serverless
  functions open a fresh DB connection per invocation and will hit Supabase's
  connection cap otherwise. `database.py` already switches to `NullPool` when
  it detects `VERCEL=1` (Vercel sets this automatically), so no extra app code
  is needed.
- **Migrations don't run automatically on deploy** — Vercel serverless
  functions aren't a place to run `alembic upgrade head` on every boot. Run
  migrations manually (step 3) whenever you add a new one, against the direct
  connection string.
- This is the **local sandbox stand-in login** (`POST /api/auth/login`), not
  real SSO — fine for a live demo, see the main `README.md` for the caveat.
