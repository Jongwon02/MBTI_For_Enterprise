# Biz-DNA (working name) — SME management diagnosis platform

Requirements: `Biz-DNA 중소기업 경영진단 플랫폼 PRD.md`. Working rules: `CLAUDE.md`.

## Run (Windows)

Double-click `run_dev.bat`. On first run it installs the Python venv and npm packages, then opens the API server (8000) and web server (3000) windows and http://localhost:3000.

To run manually:

```bash
# API (in the api folder)
../.venv/Scripts/python -m uvicorn bizdna_api.main:app --reload --port 8000
# Web (in the web folder)
npm run dev
```

Requirements: Python 3.12+, Node.js 22+.

### Member features (Supabase) locally

Sign-up, login, My Page, and the admin screen need Supabase. Without the env vars only guest diagnosis works.

```bash
npx vercel@latest env pull web/.env.local --environment development   # NEXT_PUBLIC_SUPABASE_*
npx vercel@latest env pull api/.env --environment development         # SUPABASE_URL, POSTGRES_URL*
.venv/Scripts/python scripts/migrate.py                               # apply supabase/migrations
```

Admin accounts and the `/admin` screen: `docs/admin.md`.

## Tests

```bash
.venv/Scripts/python -m pytest api      # engine and API (including reference-case regression)
cd web && npx tsc --noEmit && npm run lint && npm run build
```

## Layout

| Folder | Content |
| --- | --- |
| `api/engine/` | Diagnosis engine (Python, pure functions). Config in `api/engine/bizdna/config/*.json` |
| `api/` | FastAPI: items, diagnosis, PDF reports, member diagnoses, admin API. `api/fonts/` holds NanumGothic (OFL) for PDFs |
| `web/` | Next.js: home, survey, result dashboard, login/sign-up, My Page, admin |
| `supabase/migrations/` | DB schema, RLS, triggers, analytics store |
| `scripts/` | Migration, admin accounts, analytics backfill, dummy data |
| `docs/` | Item bank, 1.0 engine spec, design system, admin guide |
| `legacy/` | Original ChatGPT prototypes (do not modify) |
| `prototype/` | Home-page design mockup (HTML) |

## Deployment (Vercel)

The Services config in the root `vercel.json` deploys `web` (Next.js) and `api` (FastAPI) to one project (`21111/mbti-for-enterprise`). `/api/*` goes to the api service, everything else to web. Pushing to `main` auto-deploys production (https://mbti-for-enterprise-21111.vercel.app).

```bash
npx vercel@latest deploy          # preview
npx vercel@latest deploy --prod   # production
```
