# DB, sign-up/login, deployment (Supabase + Vercel)

> Moved verbatim from `CLAUDE.md` section 11 on 2026-11-23 to keep CLAUDE.md short. Subsection numbers are unchanged, so references such as "CLAUDE.md 11.x" in code comments point here. `CLAUDE.md` keeps only the must-hold rules; if the two disagree, update both.

Decided 2026-11-16: **Supabase** for DB and auth, **Vercel** for deployment. Supabase, Vercel, and Next.js 16 APIs change often, so recheck the official docs (or the installed package docs) before writing code.

## 11.1 Architecture

```
Browser ──(login, session)──▶ Supabase Auth
   │
   ▼  One Vercel project (Vercel Services)
 web service (Next.js)          api service (FastAPI, Python 3.12)
   │  sends the Supabase access token on /api/*     │
   │  as Authorization: Bearer ───────────────────▶ │ verify JWT → check permission → run engine
   │                                                ▼
   │                                      Supabase Postgres (diagnosis and company data)
```

- **Division of roles**: the browser uses Supabase **only for login**. All reads and writes of company and diagnosis data go through FastAPI, to keep permission checks (section 6) and engine execution in one place. Do not build features where the browser queries Supabase tables directly.
- **Engine location**: the engine (`api/engine/`) runs inside the API. Only answers and results go to the DB.

## 11.2 Supabase setup

- **Connection**: create the project through the Vercel Marketplace Supabase integration (Vercel Native), which registers Vercel env vars automatically.
  - Public: `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` (browser)
  - Server only: `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`, `SUPABASE_SECRET_KEY`, `POSTGRES_URL` (pooled), `POSTGRES_URL_NON_POOLING`, `POSTGRES_USER`/`POSTGRES_PASSWORD`/`POSTGRES_HOST`/`POSTGRES_DATABASE`
  - Locally, fetch them with `vercel env pull`. **`SUPABASE_SECRET_KEY` and `POSTGRES_*` are used only by the api.** Never in web code or `NEXT_PUBLIC_` variables.
  - Once connected, rename the placeholders in `api/.env.example` (`DATABASE_URL`, `BIZDNA_AUTH_SECRET`) to the names above. Supabase JWTs are used, so no self-signed key is needed.
- **Region**: Korean company data, so the recommendation was Supabase Seoul (ap-northeast-2) and Vercel functions in Seoul (icn1).
- **Connection status (2026-11-18)**: not the Marketplace integration; the user's own Supabase project `MBTI` (ref `jjjgyzmdqnskxussdhte`) is connected manually. Its region is **Mumbai (ap-south-1)**, unlike the recommendation, and **it will not be moved** (2026-11-18 user decision: migration effort outweighs the benefit). Do not propose moving the region again. DB access uses the pooler `aws-0-ap-south-1.pooler.supabase.com` (6543 = `POSTGRES_URL`, 5432 = `POSTGRES_URL_NON_POOLING`). Migrations are applied with `scripts/migrate.py`. The 6 Vercel env vars (`SUPABASE_URL`, `SUPABASE_SECRET_KEY`, `POSTGRES_URL`, `POSTGRES_URL_NON_POOLING`, `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`) are registered **for Production only**. With a single project, previews run guest diagnosis only, without member features. Local `api/.env` also holds the raw `SUPABASE_DB_PASSWORD` (git-ignored).
- **Auth settings caveat**: under Sign In / Providers, **keep the Email provider on and turn only Confirm email off.** Username login uses the Email provider internally (synthetic address). With the Email provider off, sign-up (admin API) works but login fails with `email_provider_disabled` (422) (confirmed in production 2026-11-18).
- **Migrations**: schema, RLS policies, and triggers live as SQL in `supabase/migrations/*.sql` (Supabase CLI format). Anything changed by hand in the dashboard must be moved into a migration file. No Alembic.
- **RLS is mandatory**: tables in `public` can be reached through the Data API with the publishable key, so **enable RLS on every table.** RLS with no policies blocks direct browser access while FastAPI uses a server-only DB connection. Add policies that mirror section 6 (e.g. "own company only") as defense in depth.
- **API DB connection**: FastAPI uses `POSTGRES_URL` (pooled). Keep connections short (serverless) and disable prepared statements on the transaction pooler.
- **Files**: evidence files (FR-17) and archived PDFs go in a **private** Supabase Storage bucket; the API issues short-lived signed URLs for download. While PDFs are generated per request, nothing needs storing.

## 11.3 Sign-up and login (FR-01)

- **Web (Next.js 16)**: use `@supabase/ssr`. Browser components use `createBrowserClient`; server components, server actions, and route handlers use `createServerClient`.
  - **`web/proxy.ts` is required** (Next 16's new name for middleware). It calls `supabase.auth.getClaims()` to refresh expired sessions and rewrite cookies.
  - On the server, identify users with **`getClaims()`**. Never trust `getSession()` in server code (it reads cookies without verification).
- **API (FastAPI)**: accepts `Authorization: Bearer <access token>` and verifies it against the Supabase public signing keys (`{SUPABASE_URL}/auth/v1/.well-known/jwks.json`). Cache keys in memory; refetch on an unknown `kid`. The verified `sub` is the user ID.
- **Where roles live**: roles (company, consultant, agency, admin) must be stored **where users cannot edit them**: the DB `memberships` table or Auth `app_metadata`. Never use `user_metadata` for authorization (users can change it). Check permissions against the DB on every request.
- **Sign-up flow (company representative)**:
  1. **Sign up with username and password. No email is collected and there is no email verification** (2026-11-18 decision).
  2. Collect consent for personal-data collection/use and for storing diagnosis results (`consents`). AI-analysis consent is separate.
  3. Register the company (FR-02 company info); the person signing up becomes its `owner`.
  4. Start the diagnosis. If answers saved before login exist in the browser (`bizdna.survey.v1`), offer "import these answers into my account".
- **Consultants, agencies, admins**: do not self-register. An admin invites or approves them and assigns the role (open item in section 9). **Admins** are created or granted with `scripts/grant_admin.py` (`docs/admin.md`). The first admin username is `whoami` (2026-11-18).
- **Username login (2026-11-18 decision, must hold)**: sign-up and login use **username + password only**. **Do not build email input, email verification, verification mail, or email-based password reset.** Supabase Auth only creates accounts by email, so the username is mapped to the internal address `{username}@users.bizdna.invalid` (`.invalid` is a reserved domain that never receives mail). This address is never shown; only the username is shown (`loginId`). Username rule: starts with a lowercase letter; lowercase letters, digits, underscore; 4–20 chars; input is lowercased. The rule and domain live in two places, `api/bizdna_api/signup.py` (`USERNAME_RE`, `LOGIN_DOMAIN`) and `web/lib/auth.ts` (`USERNAME_RE`, `usernameToEmail`); change them together. The username also goes into `user_metadata.username`, for display only, never for authorization. Password reset for forgotten passwords needs a mail-free method (e.g. admin reset) — not built yet. Admin passwords can be changed in the Supabase dashboard (`docs/admin.md`).
- **Current behavior (2026-11-18)**: username + password sign-up and login, **no email verification** (user decision). Sign-up is not done in the browser: `POST /api/auth/signup` creates an `email_confirm: true` account through the Supabase admin API (`SUPABASE_SECRET_KEY`), then the page signs in immediately with `signInWithPassword`, so the dashboard "Confirm email" setting does not matter. The sign-up API has no rate limit yet (consider Vercel Firewall etc. before launch). Visiting `/diagnosis` offers login, sign-up, or guest. Guests can run the whole diagnosis but answers stay in the browser. Members are saved to the server as `draft` on each step and on "중간저장" (interim save); when the basic or full diagnosis is finished, the server runs the engine and stores result and versions (`basic_completed`, `full_completed`; status never goes down). My Page shows in-progress rounds (resume) and completed rounds (view the result as saved, continue to full diagnosis, delete). Logging out clears member answers left in the browser. No social login (section 9).
- **Consent**: the 3 required consents on the sign-up page (personal data, result storage, **statistical use** (added 2026-11-18, 12.2)) are sent in `user_metadata.consents` and moved into the `consents` table by the sign-up trigger. Wording is draft (`TERMS_VERSION = 2026-11-18-draft`). Members who signed up before 2026-11-18 have no statistical-use consent and are not collected. AI consent will be added with the AI feature.
- **Auth settings**: register the production domain, `http://localhost:3000`, and Vercel preview URLs as Site URL / Redirect URLs in the Supabase dashboard. The Vercel integration creates preview-branch redirect URLs automatically. Username login sends no mail, so no SMTP is needed.
- **Account deletion**: delete personal data on account deletion. Retention and de-identification of company diagnosis data are set in the privacy policy and implemented accordingly.

## 11.4 Data model (based on PRD section 11 "data to store"; draft)

| Table | Key columns | Notes |
| --- | --- | --- |
| `profiles` | `id` (= auth.users.id), name, contact, sign-up date | Created by trigger on sign-up |
| `organizations` | name, type (agency, consultancy) | |
| `memberships` | `user_id`, `role` (company, consultant, agency, admin), `organization_id` | Source of truth for roles. **Implemented (2026-11-18)**: only `admin` is used so far |
| `companies` | company info (FR-02): industry, founding year, revenue, operating margin, headcount, customers/channels, goals, investment plans | Sensitive |
| `company_members` | `company_id`, `user_id`, `role` (owner, member) | Representative ↔ company |
| `consultant_assignments` | `consultant_id`, `company_id`, period | Consultants see only assigned companies |
| `program_enrollments` | `organization_id` (agency), `company_id`, program name | Agencies see only companies in their programs |
| `diagnoses` | `company_id`, `phase` (basic, full), `status` (draft, basic_completed, full_completed), `survey`/`progress`/`result` (jsonb), `model_version`, `questions_version`, `created_by`, created/completed timestamps | Diagnosis rounds. Results stored with versions for reproducibility. **Implemented**: until `companies` exists, permissions use `created_by` and `company_id` is empty |
| `consents` | `user_id`, `company_id`, kind (privacy, storage, AI, analytics), terms version, consented at, withdrawn at | **Implemented** |
| `audit_logs` | who viewed or changed what, when | Access log for sensitive data. **Implemented (2026-11-18)**: `private.audit_logs`, currently only admin views/exports |
| `analytics.*`, `private.subject_map` | manager-tendency data collection | Section 12. **Implemented (2026-11-18)** |
| (P1) `action_items`, `kpi_records`, `evidence_files` | 90-day action items, KPI results, evidence | |

- Items and weights stay in `api/engine/bizdna/config/*.json`. Decide whether to move them to the DB when an admin editing feature (FR-18) is built.
- Encryption: Supabase encrypts data at rest and in transit by default. Extra column-level encryption for fields like revenue and operating margin is an open item (section 9).

## 11.5 Vercel deployment

- **Layout**: a Vercel Services config at the repo root deploys `web` (Next.js) and `api` (FastAPI) as one project. Both services always deploy and roll back together.
  - Public routing: `/api/(.*)` → api service, everything else `/(.*)` → web service. Next.js has no API routes of its own, so the api owns all of `/api`. The api receives the original path (`/api/...`); FastAPI routes already start with `/api`, so no rewriting is needed.
  - Web and API share a domain, so production needs no CORS. The `/api` rewrites in `next.config.ts` and `BIZDNA_API_URL` remain for local development only.
  - The config is `vercel.json` `services` (or the recommended `vercel.ts` with `@vercel/config`). Check the latest docs before editing.
- **Deployment status (2026-11-16)**: production URL **https://mbti-for-enterprise-21111.vercel.app** (public). Vercel project `21111/mbti-for-enterprise` (framework preset `services`, Root Directory = repo root); pushing to GitHub `main` auto-deploys production. Deployment protection is `prod_deployment_urls_and_all_previews` ((Legacy) Standard Protection): only the latest production URL is public; previews and per-deployment URLs are visible to Vercel team members only. After connecting a custom domain, switching to Standard Protection is fine. Config is the root `vercel.json`. The 3 pre-deployment problems were solved as follows:
  1. **Engine import path**: `engine/` moved to `api/engine/` inside the api service bundle; `api/bizdna_api/main.py` adds it to `sys.path`.
  2. **Korean PDF font**: NanumGothic (OFL, `api/fonts/`) is committed and used by default; override with `BIZDNA_FONT_*`.
  3. **Runtime versions**: Python 3.12 (`api/.python-version`); Node `engines` ≥ 22 in `web/package.json`, project setting 26.x.
- **Files not deployed**: `.vercelignore` (excludes legacy, prototype, docs, captures, local secrets for CLI deploys). Runtime dependencies in `api/requirements.txt`, test tools in `api/requirements-dev.txt`.
- **Checking a deployment**: previews are behind Vercel auth, so use `vercel curl <path> --deployment <URL>`. In Git Bash add `MSYS_NO_PATHCONV=1` so `/api/...` is not turned into a Windows path.
- **Vercel CLI caveats**: removing env vars (`vercel env rm`) needs human approval. To change only a value, use `vercel env update <NAME> --environment production --value ... --yes`. `vercel link` creates `.env.local` (OIDC token) at the root and appends `.env*` to `.gitignore`; that line also blocks `.env.example`, so remove it.
- **Env vars**: register per Production / Preview / Development in the Vercel dashboard. Supabase integration vars are automatic; also register `BIZDNA_ENV=production`, font paths, and (later) AI keys. Connect a separate Supabase project or branch to Preview so previews never touch the production DB.
- **Limits**: function request/response bodies max 4.5 MB (current PDF ~0.15 MB). Default function timeout 300 s.
- **Preview protection**: preview deployments are visible to team members only via Vercel Deployment Protection.
- **Local development**: `run_dev.bat`, or `vercel dev` to run both services once Services is set up.

## 11.6 Implementation order (recommended)

1. Link the Vercel project, install the Supabase integration, `vercel env pull` → align `.env.example` names
2. Write the 11.4 tables and RLS in `supabase/migrations`
3. Web: `@supabase/ssr` clients, `proxy.ts`, sign-up/login/logout/password-reset screens (design: sub-page pattern in `docs/design-system.md`)
4. API: JWT verification dependency, permission checks, `/api/companies` and `/api/diagnoses` save/read, with permission tests (blocking other companies, etc.)
5. Move survey and result screens from localStorage to server storage; add import of anonymous answers
6. Solve the 3 pre-deployment problems in 11.5, check the whole flow on a preview deployment → production
