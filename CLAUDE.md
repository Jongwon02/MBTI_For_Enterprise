# CLAUDE.md

Instructions for Claude Code working in this repository. The source of detailed requirements is `Biz-DNA 중소기업 경영진단 플랫폼 PRD.md` (the PRD); if this file and the PRD conflict, the PRD wins. When a decision changes the PRD, update both the PRD and the "decisions" parts of this file.

## 1. Project overview

- **Service**: Biz-DNA (working name). A management-diagnosis website where SMEs (including startups and growth companies) answer a 100-item online survey and receive **a DNA type (16 types, MBTI-style 4-letter code), growth stage (S1–S5), scores for 8 management competences, 3 priority strategies, and a PDF report**.
- **Flow**: company info → basic diagnosis → full diagnosis → result dashboard → report → 90-day execution → re-diagnosis at 3/6/12 months.
- **4 user roles**: company representative (main user), consultant, operating agency, system administrator.
- **Out of scope (do not build)**: small-merchant (store) diagnosis, trade-area / card-sales analysis, eligibility checks for support programs, automatic external financial-data integration, AI computing scores or types directly.
- **Language**:
  - **UI copy is Korean.** Code comments and commit messages are Korean (unchanged convention).
  - **All Markdown documents (`*.md`) are written in English** (2026-11-18 user decision), including new ones. Exception: the user's PRD, and verbatim Korean source text (survey items, UI labels) quoted inside docs.
  - Code identifiers (variables, functions, tables) are English.
  - **Replies to the user in chat are Korean.**

## 2. Current status (2026-11-18)

**Diagnosis works end to end**: company info → basic diagnosis (DNA 24, stage 6, goals/obstacles) → basic result → full diagnosis (competence 64, growth plan) → result dashboard → PDF (basic and full).

| Area | Status |
| --- | --- |
| Done | FR-02 company info, FR-03 web survey (basic/full split, interim save), FR-04 completeness check and missing-value handling, FR-05–09 engine, FR-10 result dashboard, FR-11 basic PDF, FR-13 full PDF (~10 pages; target 15–20 not met) |
| Done (2026-11-17/18) | FR-01 **username + password** sign-up/login/logout (Supabase Auth, no email verification), guest diagnosis, My Page (resume drafts, view saved results, delete), FR-12 server storage of member diagnosis rounds (own rounds only) |
| Done (2026-11-18) | Manager-tendency data collection (section 12: `analytics`/`private` schemas, collected in the same transaction as the final save, backfill), admin accounts (`memberships` role admin) and admin screen `/admin` (aggregates, round list, detail, CSV, 15 s auto refresh, audit log). Usage in `docs/admin.md`. Browser tab icon is the Biz-DNA mark (`web/app/icon.svg`) |
| Missing | Consultant and agency roles (only admin exists), `companies` table, password reset, account deletion, social login, industry-specific item branching, everything from FR-14 on, AI narrative (FR-20) |
| Draft (needs user confirmation) | Stage-level wording of the 6 growth-stage items, P01–P12 options, P01→goals and P09→flags mappings (`draft: true` in `questions_v1.json`). The scope of the basic diagnosis (= DNA + stage + P01/P09) is also provisional |

- Run: `run_dev.bat` (API 8000 + web 3000). Tests: `.venv/Scripts/python -m pytest api`; in `web`: `npx tsc --noEmit && npm run lint && npm run build`. Details in `README.md`.
- Reference docs: `docs/question-bank.md` (the 100 items), `docs/engine-v1-reference.md` (1.0 calculation rules), `docs/design-system.md` (design), `docs/admin.md` (admin). Source: ChatGPT shared conversation (https://chatgpt.com/share/6af7f207-27bc-83ee-a43b-b5e628d312d2).
- `legacy/`: original 1.0/2.0 prototypes, verified to run (`legacy/README.md`). Do not modify. Engine regression tests compare against these down to strategy scores.
- `prototype/home.html`: approved home-page mockup. The real home is `web/app/page.tsx`.
- v3–v8 and the `al/` folder from later in that conversation are **for small merchants** (out of scope). Do not reference or reuse them.

## 3. Tech stack

| Area | Choice | Status |
| --- | --- | --- |
| Diagnosis engine | Python 3.12 pure-function package `api/engine/bizdna` | In use |
| API | FastAPI + Pydantic v2 (`api/bizdna_api`) | In use |
| Frontend | **Next.js 16** (App Router, cacheComponents) + React 19 + TypeScript + Tailwind 4 | In use |
| Charts | Recharts (competence radar, admin distribution bars) | In use |
| PDF | ReportLab (2.0 approach). Font lookup: `BIZDNA_FONT_REGULAR/BOLD` → Malgun Gothic → Nanum | In use |
| DB | **Supabase** (PostgreSQL; migrations in `supabase/migrations/*.sql`, applied with `scripts/migrate.py`) | In use (section 11) |
| Sign-up / login | **Supabase Auth** (web: `@supabase/ssr`; API: JWT verification with PyJWT) | In use (section 11) |
| Deployment | **Vercel** (one project with web + api services) | In use (section 11.5) |
| Tests | pytest (engine, API) | No UI tests (Playwright) |

**Next.js 16 differs from training data.** Before writing code, read the relevant doc in `web/node_modules/next/dist/docs/` (`web/AGENTS.md`). Screens that read browser storage are wrapped in `next/dynamic` `ssr: false` wrappers (`SurveyClient`, `ResultClient`, `AdminClient`) to avoid setState inside effects (eslint `react-hooks/set-state-in-effect`).

### Directory layout

```
api/engine/bizdna/  engine.py (diagnosis, strategies), survey.py (survey → engine input, completeness), config.py
  config/           model_v1.json (weights, thresholds, rules), questions_v1.json (items, draft items)
api/engine/tests/   fixtures.py (reference cases), test_regression.py (vs legacy), test_engine.py
api/bizdna_api/     main.py (/api/questions, /api/diagnose, /api/completeness, /api/report, /api/me, /api/diagnoses),
                    auth.py (JWT verification), signup.py (sign-up via admin API), store.py (diagnosis store: Postgres + in-memory for tests, collection, admin queries),
                    analytics.py (section 12 direction values, derive_rows, aggregation; pure functions), admin.py (/api/admin/*), report.py (PDF)
api/tests/          test_api.py, test_diagnoses.py (tokens, permissions), test_signup.py, test_analytics.py, test_admin.py
supabase/migrations/ schema, RLS, sign-up trigger, analytics store SQL
scripts/            migrate.py (apply migrations), grant_admin.py (admin accounts), backfill_analytics.py (analytics backfill), seed_dummy.py (create/delete dummy diagnoses)
web/app/            page.tsx (home), diagnosis/ (survey, result), login/, signup/, mypage/, admin/, icon.svg, styles/*.css
web/proxy.ts        Supabase session refresh; redirects anonymous /mypage and /admin to /login
web/components/     SiteHeader (top-right admin/login/My Page), SiteFooter, Logo, home/, auth/ (LoginForm, SignupForm),
                    survey/ (DiagnosisEntry: login/sign-up/guest choice, SurveyApp, fields), result/, mypage/, admin/ (AdminApp, charts, FactDetail)
web/lib/            api.ts, auth.ts (useAuth, token), useIsAdmin.ts, admin-types.ts, supabase/ (config, client), storage.ts (localStorage), types.ts, sample.ts, content.ts
```

- The web app forwards `/api/*` to FastAPI (`BIZDNA_API_URL`, default 127.0.0.1:8000) via rewrites in `next.config.ts`.
- The source of truth for items and weights is `api/engine/bizdna/config/`. The web app fetches items from the API. Exception: the 16-type list on the home page (`web/lib/content.ts`) is a copy; update it when type names change.
- If the survey step order changes, update `FIRST_FULL_STEP` in `web/lib/storage.ts`.
- The logo mark lives in `web/components/Logo.tsx`; `web/app/icon.svg` is a copy on a white tile. Change both together.

## 4. Diagnosis model core rules (summary of PRD section 8 — must hold in implementation)

All weights, cut-offs, and types are **hypotheses pending pilot validation**. Do not hard-code them; keep them in versioned config under `api/engine/bizdna/config/`.

**The reference implementation is the 1.0 engine.** The new engine first reproduces the calculations in `docs/engine-v1-reference.md` exactly and passes the regression cases, then fixes the differences from the PRD (marked ⚠ below) one at a time. Each fix bumps the config version; if regression expectations change, record why.

### 4.1 Items (100 items, text in `docs/question-bank.md`)
- 24 DNA items (D01–D24, 6 per axis), 64 competence items (8 per domain), 12 growth-plan/constraint items (P01–P12, **not added to scores**; used only as strategy-recommendation constraints).
- **Code scheme**: the 1.0 engine namespaces `answers.dna.D01–D24` and `answers.competence.A01–H08` to avoid collisions (finance is `D01–D08`; the design document writes D25–D32). Keep this structure in input JSON. In a DB item master, use the composite key `(section, code)`.
- Scale 1–5. Reverse items score `6 − raw`. All 24 DNA items currently have the A tendency on the right, so there are no reverse items.
- **A missing answer is missing (None), not 0.** Domain scores with missing answers are computed from answered items, and the missing ratio is recorded with the result. (Implemented: 1.0 rejected missing answers as errors; the current engine records them as missing. If a whole domain is missing it is dropped and the weights renormalized. A growth stage is assigned only when all 6 indicators are present.)
- The 6 growth-stage indicator items, the P01 goal options → engine goals mapping, and the P09 growth obstacles → risk flags mapping are **drafts**, marked `draft: true` in `questions_v1.json` (converted by `api/engine/bizdna/survey.py`). P09's `talent` and `sales_channel` have no engine flag, so they do not affect strategy scores. Keep the draft marking until the user confirms.

### 4.2 DNA types (4 axes → 16 types)
- Axes: D1 G/S (growth expansion / stability), D2 I/E (innovation & differentiation / efficiency & competition), D3 N/C (new markets / existing-market focus), D4 P/O (organizational system / founder-led).
- `D_k = Σ(x_kj − 1) / 24 × 100`
- ≥ 60 → A tendency, ≤ 40 → B tendency, 40 < x < 60 → **boundary**. If a 4-letter code is needed, classify provisionally at 50, flag the boundary, and ask confirmation items. (1.0 always assigns letters at 50 and only adds a `boundary` flag. There are no confirmation items.)
- Type code order is always `[G|S][I|E][N|C][P|O]`. The 16 type names in PRD 8.2 are authoritative (e.g. GICO = 기술중심 성장형).
- Types are not ranked. UI and report copy must not use ranking or evaluative language.

### 4.3 Eight management competences
- A strategy & business model 15, B market & customer 15, C product & technology 15, D finance & funding 15, E organization & founding team 10, F production & operations 10, G digital 5, H growth potential 15 (%, sums to 100).
- `C_d = Σ(x_i − 1) / (8 × 4) × 100`, `T = Σ W_d · C_d`
- Grades: A ≥ 85, B ≥ 70, C ≥ 55, D ≥ 40, E < 40 (lower bounds inclusive).
- Build the config so weights can vary by industry (manufacturing, services, wholesale/retail) and stage (values undecided; use defaults).

### 4.4 Growth stage S1–S5
- Weighted mean of 6 indicators (each 1–5): commercialization 20, customer validation & repeat purchase 20, revenue trend 20, revenue model & cash flow 15, organization & operations 15, market expansion & investment 10.
- **Mandatory gates override the weighted mean.** 1.0 pilot gates (applied in order): S4+ requires customer ≥ 4, revenue ≥ 4, operations ≥ 3, else S3 / S5 requires operations ≥ 4, expansion ≥ 4, else S4 / S3+ requires customer ≥ 3, revenue ≥ 2, else S2 / S2+ requires product ≥ 2, else S1. Provisional stage = `int(weighted index + 0.5)`. Record the reason when a gate adjusts the stage.
- Never assign a stage from company age alone.

### 4.5 Strategy recommendation (12 strategy groups ST01–ST12)
- `R_j = 0.30F + 0.30U + 0.25E + 0.15X` (each 0–100: fit, urgency, expected impact, feasibility).
- **Mandatory rules override weighted scores** (PRD 8.5's 6 rules, e.g. cash-flow risk → defer expansion investment). 1.0 implements them as `deferred` status plus urgency bonuses, and adds `service_overload` for 7 flags. Deferred strategies go to the end of the list with a recorded reason.
- "Lowest-scoring domain = recommendation" is wrong. Find the constraint that most blocks the growth goal.
- 1.0's actual calculation: U = Σ(100 − linked competence) × weight, F = 40 + 25 × matched goals, E = 45 + 20 × matched goals, X = 75 fixed (linked competences and goal table in reference doc section 6). ⚠ F ignores DNA type and stage, and X is a constant. Replace this when the 12-strategy matching matrix exists.
- Store for every result **the reasons, applied rule IDs, and item/weight/rule versions** (traceability).

### 4.6 Regression reference cases (must always pass after engine changes)

| Item | 그린푸드랩 | 넥스트솔루션 |
| --- | --- | --- |
| DNA | GICO | GINO |
| Stage | S3 | S4 |
| Total competence | 61.87 | 75.16 |
| Recommendations 1–3 | ST07 finance & funding → ST06 profit structure → ST08 organization & talent | ST08 organization & talent → ST09 operations → ST03 market & channels |

Inputs are generated by 1.0's `create_examples.py` from target scores (values and distribution in reference doc section 7). Port that generator as the test fixture. Also port 1.0's 6 automated tests (type, stage, top strategy; missing-answer error; range error; market-validation gate; cash-risk deferral). With missing-value handling, the "missing-answer error" test becomes a "missing recorded" test.

## 5. AI rules (FR-20, PRD section 9)

- **Only the engine** produces scores, types, stages, and strategies. AI only interprets and narrates engine results and elaborates execution plans.
- Never fabricate revenue or financial figures that were not entered. Mark uncertain analysis separately.
- Without user consent or an API key, generate the rule-based report only (everything works without AI).
- Send AI only the diagnosis results needed for interpretation; never identifying data such as company name or contact details.
- AI provider is undecided (the prototype uses OpenAI `gpt-4.1-mini`, called only for the full report). Keep it behind an adapter interface so the provider is easy to swap. Use 1.0's payload scope (dna, competence, stage, risks, top 3 strategies, goals) and prompt constraints as the baseline, except that 1.0 sends the whole `company` object; remove the company name.

## 6. Security and data (PRD section 10)

- Access: companies see only themselves, consultants only assigned companies, agencies only companies in their programs. **Apply permission filters server-side on every read API** and write permission tests with them.
- Encrypt sensitive fields such as financials. Until permissions and encryption are in place, do not load real company data (test with fictitious companies only).
- Aggregate statistics must be de-identified (no small-group exposure); comparisons use similar industry/size peer groups.
- Record consent for storage and AI analysis.
- Secrets and API keys live only in `.env` files and are never committed. API: `api/.env` (read by `bizdna_api/settings.py`); web: `web/.env.local`. Only `.env.example` files are committed; when adding an env var, add it there with an empty value. Do not put secrets on the web side; `NEXT_PUBLIC_` variables are public in the browser and must never hold secrets. In production set `BIZDNA_ENV=production` (hides API docs) and `BIZDNA_CORS_ORIGINS` for the real domain.

## 7. UI and design principles

- **The design reference is `docs/design-system.md`.** It borrows layout, color, type, components, and motion from the Vista Consulting Group site (https://vistacg.co.kr/, captures in `홈페이지양식/`). Check its tokens and patterns before building a screen.
- Core tokens: text `#1d1d1f`, accent blue `#0071e3`, gray background `#f5f5f7`, secondary text `#86868b`, black section `#000`, sub-hero navy `#0a1628`, footer `#0f0f11`. Font Pretendard, headings weight 800 with tight tracking, card radius 30px, container max 1280px.
- **No copying**: do not use the VCG logo, company name, copy, or photos, or logos of public agencies (logos of organizations we have no partnership with are misleading). Do not invent track-record numbers. Where Vista shows track-record stats, show the model spec (16 types, 8 competences, 5 stages, 12 strategies).
- PDF reports use the same blue and navy as the web. 2.0's teal `#0D838B` is only a secondary chart color.
- Responsive for PC and mobile. The 100-item survey is paginated by domain with a progress indicator and **interim save**.
- Result screen: DNA 4-letter code and type name (MBTI-style card), 4-axis tendency bars (with boundary marking), 8-competence radar, growth-stage progress bar, core problems, 3 priority strategies with reasons.
- Show a "hypothetical model, pending pilot validation" notice on results and reports.

## 8. Development priorities (PRD section 12)

1. **Design deliverables first**: the 100-item scoring rubric and the 12-strategy matching matrix are top priority (the engine cannot be completed without them). If content is not in the PRD, do not invent it; mark it as draft or ask the user.
2. **MVP = P0 (FR-01–FR-12)**: launch blockers are FR-01 accounts, FR-03 web survey, FR-12 storage and permissions.
3. P1 (consultant screens, action items, re-diagnosis, full report, evidence, versioning, agency screens) → P2 (AI narrative, support-program recommendations, Word export, etc.).

Put the FR ID in commit and PR descriptions when implementing a feature (e.g. `FR-05 DNA 경계 성향 판정`).

## 9. Open decisions (PRD section 13 — record here when decided)

- [ ] Target scope: all SMEs vs startups and growth companies
- [ ] First industries: manufacturing, services, wholesale/retail all vs manufacturing first
- [ ] Revenue model: free basic + paid full vs institutional sales
- [x] UI technology: Next.js 16 + FastAPI (2026-11-16)
- [x] DB and auth: Supabase (PostgreSQL + Supabase Auth); deployment: Vercel (2026-11-16)
- [x] Login method: **username + password only, no email verification** (2026-11-17 no email verification; 2026-11-18 username instead of email). Emails are not collected. No social login (revisit only if requested again)
- [x] Anonymous trial scope: **guests may run the full diagnosis (basic, full, PDF)**; answers stay in the browser only and there is no My Page (2026-11-17)
- [ ] How consultant and agency accounts are issued: admin invitation only vs request and approval (11.3)
- [ ] Extra column-level encryption of sensitive financial fields (11.4)
- [ ] AI provider and payload scope
- [ ] Pilot sample and partner organizations
- [ ] Success metrics and performance targets
- [ ] Service name (Biz-DNA is a working name — managed as config in code)
- [ ] For manager-tendency data collection (analytics store): consent wording/privacy policy, encryption of raw financial values, aggregation bins (12.10). The collection approach was confirmed 2026-11-18 (12.2); the region stays Mumbai (2026-11-18)

Work affected by these items must not settle them unilaterally; state assumptions or ask the user.

## 10. Working rules

- Engine logic change → all of `api/engine/tests` and the regression cases must pass before reporting completion.
- Weight, threshold, or item change → bump the config version; past rounds must remain reproducible with their original version.
- Missing values and boundaries (40, 60, grade cut-offs) must have unit tests.
- In user-facing copy, consider "경영자" (manager) instead of "창업자" (founder) depending on context (fit risk for mature companies).
- Never write copy that claims a causal effect of consulting.
- **Write Markdown docs in English; reply to the user in Korean** (1).

## 11. DB, sign-up/login, deployment (Supabase + Vercel)

Decided 2026-11-16: **Supabase** for DB and auth, **Vercel** for deployment. Supabase, Vercel, and Next.js 16 APIs change often, so recheck the official docs (or the installed package docs) before writing code.

### 11.1 Architecture

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

### 11.2 Supabase setup

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

### 11.3 Sign-up and login (FR-01)

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

### 11.4 Data model (based on PRD section 11 "data to store"; draft)

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

### 11.5 Vercel deployment

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

### 11.6 Implementation order (recommended)

1. Link the Vercel project, install the Supabase integration, `vercel env pull` → align `.env.example` names
2. Write the 11.4 tables and RLS in `supabase/migrations`
3. Web: `@supabase/ssr` clients, `proxy.ts`, sign-up/login/logout/password-reset screens (design: sub-page pattern in `docs/design-system.md`)
4. API: JWT verification dependency, permission checks, `/api/companies` and `/api/diagnoses` save/read, with permission tests (blocking other companies, etc.)
5. Move survey and result screens from localStorage to server storage; add import of anonymous answers
6. Solve the 3 pre-deployment problems in 11.5, check the whole flow on a preview deployment → production

## 12. Manager-tendency data collection (diagnosis analytics store) (implemented 2026-11-18)

> **Implemented and applied to the production DB on 2026-11-18.** Migration `supabase/migrations/20261118000000_analytics_admin.sql`; code `api/bizdna_api/analytics.py`, `store.py`, `admin.py`; backfill `scripts/backfill_analytics.py`. Admin screen and accounts: `docs/admin.md`. Deviations from the design are in 12.13.

### 12.1 Purpose

Turn members' diagnoses into "meaningful information".

| Use | Examples | Basis |
| --- | --- | --- |
| Peer comparison and aggregation | DNA direction distribution, competence quantiles, obstacle/goal/policy-need distributions by industry, size, age, stage | FR-19, PRD section 10 "peer comparison, de-identified aggregation" |
| Change tracking | Changes in type, direction, stage, and scores at re-diagnosis; type stability (test-retest); completion, full-diagnosis conversion, and re-diagnosis rates | FR-16, PRD section 3 usage metrics |
| Model validation (partial) | DNA boundary ratio, growth-stage gate frequency, strategy recommendation/deferral frequency, evidence for re-weighting | PRD section 3 validation metrics |

Item-level reliability (Cronbach's α, item discrimination) cannot be computed from this store because item answers are not stored (12.2). Add them via 12.9 if needed.

### 12.2 Decisions (2026-11-18, confirmed by the user)

| Item | Decision |
| --- | --- |
| Collection function | `derive_rows(diagnosis, *, subject_key, round_no)` **pure function**. The caller, which knows the DB, supplies the pseudonymous key and round number. No DB or HTTP dependency (same style as the engine) |
| Round granularity | **One row per diagnosis round, final state.** If a round completes the basic diagnosis and later the full one, the basic row is overwritten. Unique key `(diagnosis_id, model_version)`. People who stop after basic are counted with `funnel_events` |
| Manager tendency (DNA) | Do not store the 24 answers; store only the **4 axis direction values** (12.4). Axis scores, type letters, and boundary status can be derived from them |
| Other values | **Stored raw, not binned** (founding year, revenue, previous revenue, operating margin, headcount, 6 stage indicators, raw P answers, engine scores). Bins are used only at aggregation/display (12.8) |
| Competence | Do not store the 64 answers; store the engine's 8 domain scores, total, and grade. Competence is a "level", not a "direction", so keep 0–100 scores |
| Item-level answers | Not stored in the analytics store. The originals remain in `public.diagnoses.survey`, so they can be backfilled later (12.9) |
| Identifying data | Extract only whitelisted values (12.5). Never company name, free text, or member ID |
| Statistical-use consent | **Part of the required sign-up consents** (2026-11-18 user decision). A [필수] statistical-use consent was added to the sign-up page |
| Deletion | **Analytics rows remain even if a member deletes a round or their account** (2026-11-18 user decision). On account deletion only `private.subject_map` is removed, leaving rows pseudonymous |
| Admin screen | **Aggregates + individual round list and detail** on screen (2026-11-18 user decision). Company names and usernames are never shown, and views are audit-logged |

### 12.3 Principles

1. **Separate source and analytics.** `public.diagnoses` is the service source of truth. Analytics rows are **derived** from it and must be deletable and rebuildable by backfill at any time.
2. **Extract by whitelist only.** Never copy the source (`survey`, `result`) wholesale or build rows by "removing unneeded keys" (blacklist). New engine fields stay out unless whitelisted. In particular `result.company` and `survey.company` contain the company name and free text.
3. **Link people only by pseudonymous key.** Analytics tables have no `auth.users.id`, only `subject_key`. The member ↔ key map lives in a separate `private` schema.
4. **Do not expose analytics schemas.** `analytics` and `private` are not in the Supabase Data API exposed schemas; every table has RLS on (no policies) and `anon`/`authenticated` privileges revoked. Access is only through FastAPI's server connection (same principle as 11.1).
5. **Only consented rounds.** Only final-saved rounds of members with statistical-use consent (`consents.kind = 'analytics'`, not withdrawn) are stored. This consent is required at sign-up (12.2). Stored rows remain after round or account deletion (12.2).
6. **Store versions too.** Every row has `model_version` and `questions_version`. Recomputing old rounds with a new model adds new-version rows instead of overwriting. Aggregations never mix versions.
7. **No guest diagnoses.** Guest answers live only in the browser (section 9 decision).
8. **Raw values stored, exposure only through aggregates.** Raw values such as revenue and founding year can identify a company. Individual rows leave the system only through admin access (audit-logged); screens and reports show only binned aggregates, and cells with fewer than `k` samples (hypothesis 5) are hidden.

### 12.4 DNA direction-value algorithm

Each of the 4 axes is stored as one **direction value**: its sign gives the side and its magnitude the strength, and the axis score can be recovered exactly.

**Compute (on write)**

```
axis score D_k = engine result result.dna.axes[axis].score   (0–100, 2 decimals, formula in 4.2)
direction dir_k = (D_k − 50) × 2                              (−100 to +100)
axis with no answers (score = null) → dir_k = null, answered = 0
```

- `+` is the A tendency (G growth expansion, I innovation & differentiation, N new markets, P organizational system), `−` the B tendency (S stability, E efficiency & competition, C existing-market focus, O founder-led), `0` exact center.
- `+100` means all 6 items of the axis answered 5; `−100` all answered 1.
- Axis scores have 2 decimals, so direction values are exact to 2 decimals (`numeric(5,2)`). Compute from the engine's rounded `score`, not a float, to avoid rounding drift.

**Derive (on read)**

```
axis score  = 50 + dir_k / 2
type letter = A if dir_k ≥ (letter_cutoff − 50) × 2 else B      (letter_cutoff currently 50 → dir_k ≥ 0)
boundary    = (b_threshold − 50) × 2 < dir_k < (a_threshold − 50) × 2   (currently 40/60 → −20 < dir_k < +20)
strength    = |dir_k|
```

- Type letters and boundary flags are **not stored.** The cut-offs (`letter_cutoff`, `a_threshold`, `b_threshold`) are hypotheses, so they are read from that row's `model_version` config at query time. Changing cut-offs then needs no data rebuild.
- The 4-letter `dna_type` is stored as the engine produced it (index for per-type aggregation). A mismatch with derived letters is a bug (tested).
- Only **axis scores** can be recovered; individual item answers cannot.

**Implementation (`api/bizdna_api/analytics.py`)**

```python
def axis_direction(score: float | None) -> float | None:
    """Axis score (0–100) → direction value (−100–+100)."""
    return None if score is None else round((score - 50) * 2, 2)


def axis_score(direction: float | None) -> float | None:
    """Direction value → axis score. axis_score(axis_direction(s)) == s must hold."""
    return None if direction is None else round(50 + direction / 2, 2)
```

**Example** (그린푸드랩-like): G/S 75 → `+50`, I/E 68 → `+36`, N/C 42 → `−16` (boundary), P/O 30 → `−40`. Stored: `dna_type = 'GICO'`, `dna_g_dir = 50.00`, `dna_i_dir = 36.00`, `dna_n_dir = -16.00`, `dna_p_dir = -40.00`.

**Required unit tests**: round trip (`axis_score(axis_direction(s)) == s` for 0, 40, 50, 60, 100 and fractional scores), unanswered axis (null), boundaries (scores 40/60 → directions −20/+20 are not boundary), engine `dna_type` matches derived letters.

### 12.5 Whitelist (source → analytics column)

Anything not in this table is dropped.

| Source | Analytics column | Handling |
| --- | --- | --- |
| `diagnoses.id` | `diagnosis_id` | For backfill/rebuild. Excluded from analyst-facing output |
| `diagnoses.created_by` | — | Dropped. The caller converts it to `subject_key` |
| `diagnoses.company_name`, `progress`, `status` | — | Dropped |
| `diagnoses.phase`, `model_version`, `questions_version`, `completed_at` | same names | Raw |
| `survey.company.industry` | `industry` | Raw (제조업, 서비스업, 도소매업) |
| `survey.company.founded_year` | `founded_year` | Raw |
| `survey.company.sales_recent`, `sales_prev` | `sales_recent`, `sales_prev` | Raw (100M KRW) |
| `survey.company.operating_margin` | `operating_margin` | Raw (%) |
| `survey.company.employees` | `employees` | Raw (people) |
| `survey.company.customer_type` | `customer_type text[]` | Raw (options) |
| `survey.company.name`, `industry_detail`, `main_channel`, `goal_3y`, `investment_plan` | — | **Dropped** (company name, free text) |
| `survey.answers.dna.*` (24 items) | — | Not stored → direction values from `result.dna` |
| `survey.answers.competence.*` (64 items) | — | Not stored → domain scores from `result.competence` |
| `survey.answers.stage.{product, customer, revenue, cash, operations, expansion}` | `stage_product` … `stage_expansion` | Raw 1–5 |
| `survey.answers.plan.P01`–`P12` | `plan jsonb` | Only P-code keys, raw values (option-code arrays, numeric amounts/headcounts) |
| `survey.answers.plan.P01` | `goals text[]` | Raw (copy for indexing/aggregation) |
| `survey.answers.plan.P09` codes present in `model.risks` | `risk_flags text[]` | Engine risk-flag codes. `result.risks` holds Korean labels, so it is not used |
| `result.dna.type` | `dna_type` | Raw |
| `result.dna.axes[axis].score` | `dna_g_dir`, `dna_i_dir`, `dna_n_dir`, `dna_p_dir` | 12.4 direction values |
| `result.dna.axes[axis].answered` | `dna_g_answered` … `dna_p_answered` | Raw (0–6) |
| `result.stage.code`, `weighted_index`, `provisional`, `gate_adjusted`, `gates_applied[].id` | `stage_code`, `stage_weighted_index`, `stage_provisional`, `stage_gate_adjusted`, `stage_gates text[]` | Raw |
| `result.competence.total`, `grade.grade`, `missing_ratio` | `total_score`, `grade`, `competence_missing_ratio` | Raw (full diagnosis only; null for basic) |
| `result.competence.domains[A–H]` | `analytics.domain_scores`, 8 rows | Raw score, that round's weight, answered count (8 − number of `missing` in that domain) |
| `result.strategies[]` `code`, `factors.{fit, urgency, impact, feasibility}`, `score`, rank, `status`, `applied_rules` | `analytics.strategy_scores`, 12 rows | Raw. Rank = list order (from 1) |
| `result.dna.name`, `profile`, `strategies[].name`/`reasons`/`actions`/`kpis`, `result.company`, `result.plan`, `limitations`, `completeness` | — | **Dropped** (labels come from config; the rest is duplicate or identifying) |

### 12.6 DB setup (migration)

One migration file (`supabase/migrations/<timestamp>_analytics.sql`), applied with `scripts/migrate.py`. Never created by hand in the dashboard (11.2).

**Order**

1. Create schemas `private` and `analytics` → revoke privileges
2. Add `'analytics'` to `public.consents.kind` (change the existing check constraint)
3. Create `private.subject_map` → `analytics.*` tables
4. Enable RLS on all new tables (no policies), create indexes
5. Create the pseudonymous-key function `private.get_subject_key(user_id)`
6. Verify after applying: Supabase dashboard Settings → API **Exposed schemas does not include `analytics` or `private`**, and calling `/rest/v1/diagnosis_facts` with the publishable key is refused

**SQL draft**

```sql
-- 1. Schemas and privileges -------------------------------------------------------
create schema if not exists private;
create schema if not exists analytics;
revoke all on schema private, analytics from public, anon, authenticated;
alter default privileges in schema private, analytics revoke all on tables from public, anon, authenticated;

-- 2. Add the statistical-use consent kind ------------------------------------------
alter table public.consents drop constraint if exists consents_kind_check;
alter table public.consents add constraint consents_kind_check
  check (kind in ('privacy', 'storage', 'ai', 'analytics'));

-- 3. Pseudonymous key map (deleted with the member, leaving analytics rows unlinkable) --
create table private.subject_map (
  user_id     uuid primary key references auth.users (id) on delete cascade,
  subject_key uuid not null unique default gen_random_uuid(),
  created_at  timestamptz not null default now()
);

-- 4. Diagnosis round facts (one row per round × model version) ----------------------
create table analytics.diagnosis_facts (
  fact_id            uuid primary key default gen_random_uuid(),
  diagnosis_id       uuid not null,            -- no FK: source rows may be deleted (12.2)
  model_version      text not null,
  questions_version  text not null,
  subject_key        uuid not null,
  round_no           int  not null check (round_no >= 1),
  phase              text not null check (phase in ('basic', 'full')),
  completed_at       timestamptz not null,
  -- company info (raw)
  industry           text,
  founded_year       int,
  sales_recent       numeric,
  sales_prev         numeric,
  operating_margin   numeric,
  employees          int,
  customer_type      text[],
  -- manager tendency (12.4 direction values)
  dna_type           text,
  dna_g_dir          numeric(5,2) check (dna_g_dir between -100 and 100),
  dna_i_dir          numeric(5,2) check (dna_i_dir between -100 and 100),
  dna_n_dir          numeric(5,2) check (dna_n_dir between -100 and 100),
  dna_p_dir          numeric(5,2) check (dna_p_dir between -100 and 100),
  dna_g_answered     smallint not null default 0,
  dna_i_answered     smallint not null default 0,
  dna_n_answered     smallint not null default 0,
  dna_p_answered     smallint not null default 0,
  -- growth stage (raw)
  stage_product      smallint, stage_customer smallint, stage_revenue smallint,
  stage_cash         smallint, stage_operations smallint, stage_expansion smallint,
  stage_code         text,
  stage_weighted_index numeric,
  stage_provisional  text,
  stage_gate_adjusted boolean,
  stage_gates        text[],
  -- competence summary (full diagnosis only)
  total_score        numeric,
  grade              text,
  competence_missing_ratio numeric,
  -- growth plan and constraints (raw)
  goals              text[],
  risk_flags         text[],
  plan               jsonb,
  created_at         timestamptz not null default now(),
  updated_at         timestamptz not null default now(),
  unique (diagnosis_id, model_version)
);

create table analytics.domain_scores (
  fact_id  uuid not null references analytics.diagnosis_facts (fact_id) on delete cascade,
  domain   char(1) not null check (domain in ('A','B','C','D','E','F','G','H')),
  score    numeric,                 -- null if the whole domain is missing
  weight   numeric not null,        -- weight in that round's model version
  answered smallint not null,
  primary key (fact_id, domain)
);

create table analytics.strategy_scores (
  fact_id     uuid not null references analytics.diagnosis_facts (fact_id) on delete cascade,
  strategy    text not null,        -- ST01–ST12
  fit         numeric, urgency numeric, impact numeric, feasibility numeric,
  total       numeric not null,
  rank        smallint not null,
  status      text not null check (status in ('recommended', 'deferred')),
  rule_ids    text[] not null default '{}',
  primary key (fact_id, strategy)
);

create table analytics.funnel_events (
  id           bigint generated always as identity primary key,
  subject_key  uuid not null,
  diagnosis_id uuid not null,
  event        text not null check (event in ('started', 'basic_completed', 'full_completed', 'report_downloaded')),
  occurred_at  timestamptz not null default now()
);

-- 5. RLS (no policies = Data API blocked; only FastAPI's server connection) ----------
alter table private.subject_map        enable row level security;
alter table analytics.diagnosis_facts  enable row level security;
alter table analytics.domain_scores    enable row level security;
alter table analytics.strategy_scores  enable row level security;
alter table analytics.funnel_events    enable row level security;

-- 6. Indexes ------------------------------------------------------------------------
create index on analytics.diagnosis_facts (industry, stage_code);
create index on analytics.diagnosis_facts (dna_type);
create index on analytics.diagnosis_facts (subject_key, round_no);
create index on analytics.diagnosis_facts (model_version);
create index on analytics.funnel_events (subject_key, event);

-- 7. Pseudonymous key (create if missing, else return existing) ------------------------
create or replace function private.get_subject_key(p_user_id uuid) returns uuid
language sql as $$
  with ins as (
    insert into private.subject_map (user_id) values (p_user_id)
    on conflict (user_id) do nothing
    returning subject_key
  )
  select subject_key from ins
  union all
  select subject_key from private.subject_map where user_id = p_user_id
  limit 1;
$$;
revoke all on function private.get_subject_key(uuid) from public, anon, authenticated;
```

`gen_random_uuid()` is built into Supabase Postgres. Before applying, confirm the existing consents check constraint is named `consents_kind_check` (drop it by its actual name otherwise).

### 12.7 Collection flow (API)

```
Final save (POST/PUT /api/diagnoses, complete=basic|full)
  ① save survey, result, versions to public.diagnoses (as before)
  ② in the same transaction:
     - check statistical-use consent: a consents row with kind='analytics', withdrawn_at is null → else stop
     - subject_key = private.get_subject_key(user_id)
     - round_no  = existing fact's round_no for this diagnosis_id,
                   else coalesce(max(round_no), 0) + 1  (per subject_key)
     - rows = derive_rows(diagnosis_row, subject_key=..., round_no=...)
     - upsert diagnosis_facts: on conflict (diagnosis_id, model_version) do update
     - domain_scores, strategy_scores: delete rows for that fact_id and reinsert
     - append basic_completed or full_completed to funnel_events
```

- `derive_rows` and the direction functions live in `api/bizdna_api/analytics.py`. The engine (`api/engine`) is not changed. Return type is the dataclass `AnalyticsRows(fact: dict, domain_scores: list[dict], strategy_scores: list[dict])`; for a basic diagnosis (`result.competence` is null) both lists are empty.
- ① and ② run in one transaction (`PostgresStore._conn` is a context manager; `create`/`update` call `_collect` inside it). `MemoryStore` mimics the same behavior for tests.
- Analytics failure fails the diagnosis save too (same transaction, so source and analytics never diverge).
- Interim saves (`draft`) create no fact. Creating a round (`POST`) records a `started` event for consenting members. Recording `report_downloaded` on PDF download needs `/api/report` to know the member — later.
- **Consent withdrawal**: statistical-use consent is a required sign-up consent, so no withdrawal feature was built. If one is added, decide again whether to delete analytics rows (the 12.2 decision is "keep").
- **Backfill**: `scripts/backfill_analytics.py` walks consenting members' completed rounds (`status in ('basic_completed','full_completed')`) in `completed_at` order and runs the same upsert. Running it repeatedly yields the same result (idempotent). To recompute with a new model version, rerun the engine and add new `model_version` rows.

### 12.8 Aggregate views (examples)

Individual rows are raw, but only these aggregates go to screens, reports, and agencies. Bin edges are hypotheses, so they belong in `api/engine/bizdna/config/analytics_v1.json` (new), read by the aggregation functions. Draft: age <3, 3–7, 7–15, 15+ years (completion year − founding year); headcount <5, 5–9, 10–49, 50–299, 300+; revenue <1, 1–10, 10–50, 50–120, 120+ (100M KRW); growth decline (<−5%), flat, growth (+5–30%), high growth (30%+); margin loss, 0–5, 5–10, 10+%; `k = 5`. All bins include the lower bound and exclude the upper.

| View | Content | Used by |
| --- | --- | --- |
| `v_dna_direction` | 4-axis direction mean/distribution, type frequency, boundary ratio by industry, stage, size | Agency screen (FR-19), "managers in the same industry" on the result screen |
| `v_domain_percentiles` | Competence domain quantiles (p25, p50, p75) by industry, size, stage | Peer comparison in results and reports |
| `v_stage_gates` | Gate frequency and 6-indicator distribution by stage | Growth-stage model review |
| `v_strategy_frequency` | Rank 1–3 recommendation frequency per strategy, deferral reasons | Strategy matrix review |
| `v_constraints` | Distribution of obstacles (P09), goals (P01), support needs (P12) | Policy-need analysis (FR-19) |
| `v_retest` | Consecutive round pairs per `subject_key`: type match, per-axis direction change, stage/score change, interval | Type stability, re-diagnosis change (FR-16) |
| `v_funnel` | Monthly start → basic done → full done, re-diagnosis rate | Usage metrics |

- Every aggregate returns sample size `n`; cells with `n < k` are hidden or merged into a parent category **in the API** (not in views, so it cannot be bypassed).
- Never mix model versions in one aggregate.
- Heavy views become materialized views refreshed daily (Vercel Cron or `pg_cron`, 12.10).

### 12.9 Access and future additions

- **Admin**: sees all aggregates and individual fact rows (list, detail) on screen and exports CSV (changed by the 2026-11-18 decision). Each view and export is logged in `private.audit_logs`. The admin screen does not apply `k` hiding but shows `n` (`docs/admin.md`).
- **Agency**: sees **aggregates only** for companies in its programs (`program_enrollments`). Build after `memberships` roles for agencies exist.
- **Consultant**: sees assigned companies via the source (`public.diagnoses`) and receives only peer-comparison values from the analytics store.
- **Company representative**: sees only peer comparisons (quantiles, ratios) on their own result screen.
- Never give external analysis tools a DB account. If needed, create a read-only role restricted to `analytics` views.
- **If item-level answers are needed** (pilot α, discrimination): add `analytics.answer_items(fact_id, section, code, value, scored, is_missing)` and fill by backfill. Rounds deleted from the source cannot be recovered.

### 12.10 Open items (confirm with the user before implementing)

- [x] Statistical-use consent: part of the required sign-up consents (2026-11-18). How to obtain it from earlier members is undecided (they are not collected now)
- [x] Analytics rows on round deletion / account deletion: kept (pseudonymous) (2026-11-18). The privacy policy must say so
- [x] Analytics failure fails the diagnosis save: implemented as one transaction (2026-11-18)
- [ ] Column-level encryption of raw financial fields such as revenue and operating margin (decide with sections 9 and 11.4)
- [ ] Final aggregation bins and the small-group threshold `k` (12.8 draft)
- [ ] Whether and how to share pilot raw data with external researchers
- [ ] Aggregate refresh cadence and tool (Vercel Cron vs `pg_cron`)
- [x] Collection function shape, one row per round, DNA direction values, raw values, no item answers (2026-11-18, 12.2)
- [x] DB region: keep Mumbai (ap-south-1) (2026-11-18, 11.2)

### 12.11 Implementation order (recommended)

1. Settle the 12.10 consent and deletion policies first.
2. Write and apply the 12.6 migration; confirm the Data API does not expose it.
3. `analytics.py`: `axis_direction`, `axis_score`, `derive_rows` + unit tests (12.4 required items, basic/full, missing axes/domains, **no non-whitelisted value in rows**: feed company names, free text, and member ID strings and scan the whole output).
4. Upsert in the same transaction in the final-save API. Tests for permissions and missing consent.
5. Fill existing rounds with the backfill script (idempotency test).
6. Aggregate views and admin query API (with `k` handling), then the agency screen (FR-19) and peer comparison on the result screen.

### 12.12 Things to know about the current storage structure

- `public.diagnoses.result` contains the engine output's full `company` (with company name), and `survey.company` also holds the company name and free text. The derivation function must extract only via the 12.5 whitelist.
- `diagnoses.company_id` is still empty. The pseudonymous key is **per member** for now, so a company re-diagnosed by a different representative looks like a different person. When `companies` exists, decide whether to key by company (better for re-diagnosis tracking).

### 12.13 Deviations from the design during implementation (2026-11-18)

- **Migration**: in addition to the 12.6 SQL, it adds `public.memberships` (admin role), `private.audit_logs`, `analytics` consent handling in the sign-up trigger, and `unique (diagnosis_id, event)` on `funnel_events` (re-saving does not add events).
- **Events**: saving a full completion also records `basic_completed` (full implies basic), so "basic done ≥ full done" holds.
- **Raw P answers**: even for whitelisted keys, only values matching the config (`questions_v1.json`) options or number format are kept, so free strings cannot slip in. Industry and customer type values not among the options are dropped too.
- **Transaction protection**: a pooler connection once dropped mid-transaction and left a lock held on the DB side. Every API transaction sets `lock_timeout 5s`, `idle_in_transaction_session_timeout 20s`, `statement_timeout 20s` via `set_config(..., true)`. Competence and strategy rows are inserted in one statement each to reduce round trips.
- **Aggregation location**: instead of the 12.8 DB views, the API currently reads the matching rows (up to 5,000) and computes with `summarize_facts`. Move to views / materialized views when rounds grow.
- **Dummy data**: `scripts/seed_dummy.py` creates fictitious `dummy_` members with consent and runs them through the real save path. 100 rounds (73 members) were loaded into the production DB on 2026-11-18 for testing; remove them with `--clean` before real operation.
