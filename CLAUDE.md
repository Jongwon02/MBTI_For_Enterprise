# CLAUDE.md

Instructions for Claude Code working in this repository. The source of detailed requirements is `Biz-DNA 중소기업 경영진단 플랫폼 PRD.md` (the PRD); if this file and the PRD conflict, the PRD wins. When a decision changes the PRD, update both the PRD and the "decisions" parts of this file.

## 1. Project overview

- **Service**: Biz-DNA (working name). A management-diagnosis website where SMEs (including startups and growth companies) answer a 100-item online survey and receive **a DNA type (16 types, MBTI-style 4-letter code), growth stage (S1–S5), scores for 8 management competences, 3 priority strategies, and a PDF report**.
- **Flow**: company info → basic diagnosis → full diagnosis → result dashboard → report → 90-day execution → re-diagnosis at 3/6/12 months.
- **4 user roles**: company representative (main user), consultant, operating agency, system administrator.
- **Out of scope (do not build)**: small-merchant (store) diagnosis in this product (it is a separate product under `sosang/`, section 13), trade-area / card-sales analysis, eligibility checks for support programs, automatic external financial-data integration, AI computing scores or types directly.
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
| Done (2026-11-24) | Site entry: `/` is a chooser between the SME diagnosis (home moved to `/sme`) and the small-merchant diagnosis (`/sosang`, separate app). Root `vercel.json` registers `sosang-web` and `sosang-api` services |
| Done (2026-11-18) | Manager-tendency data collection (section 12: `analytics`/`private` schemas, collected in the same transaction as the final save, backfill), admin accounts (`memberships` role admin) and admin screen `/admin` (aggregates, round list, detail, CSV, 15 s auto refresh, audit log). Usage in `docs/admin.md`. Browser tab icon is the Biz-DNA mark (`web/app/icon.svg`) |
| Missing | Consultant and agency roles (only admin exists), `companies` table, password reset, account deletion, social login, industry-specific item branching, everything from FR-14 on, AI narrative (FR-20) |
| Draft (needs user confirmation) | Stage-level wording of the 6 growth-stage items, P01–P12 options, P01→goals and P09→flags mappings (`draft: true` in `questions_v1.json`). The scope of the basic diagnosis (= DNA + stage + P01/P09) is also provisional |

- Run: `run_dev.bat` (API 8000 + web 3000). Tests: `.venv/Scripts/python -m pytest api`; in `web`: `npx tsc --noEmit && npm run lint && npm run build`. Details in `README.md`.
- Reference docs: `docs/question-bank.md` (the 100 items), `docs/engine-v1-reference.md` (1.0 calculation rules), `docs/design-system.md` (design), `docs/admin.md` (admin), `docs/infra.md` (section 11 full text), `docs/analytics-store.md` (section 12 full text). Source: ChatGPT shared conversation (https://chatgpt.com/share/6af7f207-27bc-83ee-a43b-b5e628d312d2).
- `legacy/`: original 1.0/2.0 prototypes, verified to run (`legacy/README.md`). Do not modify. Engine regression tests compare against these down to strategy scores.
- `prototype/home.html`: approved home-page mockup. The real SME home is `web/app/sme/page.tsx`; `/` (`web/app/page.tsx`) is the diagnosis chooser.
- v3–v8 and the `al/` folder from later in that conversation are **for small merchants**. Do not use them in this product; the small-merchant product lives in `sosang/` (section 13).

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
web/app/            page.tsx (chooser: SME vs small merchant), sme/ (SME home), diagnosis/ (survey, result), login/, signup/, mypage/, admin/, icon.svg, styles/*.css
web/proxy.ts        Supabase session refresh; redirects anonymous /mypage and /admin to /login
web/components/     SiteHeader (top-right admin/login/My Page), SiteFooter, Logo, home/, auth/ (LoginForm, SignupForm),
                    survey/ (DiagnosisEntry: login/sign-up/guest choice, SurveyApp, fields), result/, mypage/, admin/ (AdminApp, charts, FactDetail)
sosang/             small-merchant product (section 13, own CLAUDE.md)
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

## 11. DB, sign-up/login, deployment (Supabase + Vercel) — full text in `docs/infra.md`

Subsections 11.1–11.6 (architecture, Supabase setup, sign-up/login, data model, Vercel deployment, implementation order) live in `docs/infra.md` with the same numbers. Read it before touching auth, DB, migrations, env vars, or deployment. Must-hold rules:

- **Browser uses Supabase only for login.** All company/diagnosis reads and writes go through FastAPI (permission checks and engine in one place). RLS on every table; FastAPI uses a server-only DB connection (`POSTGRES_URL`, pooled, no prepared statements).
- **Secrets**: `SUPABASE_SECRET_KEY` and `POSTGRES_*` are api-only, never in web code or `NEXT_PUBLIC_`. The 6 Supabase env vars are registered for **Production only**, so previews run guest diagnosis only.
- **Supabase project** `MBTI` (ref `jjjgyzmdqnskxussdhte`), region **Mumbai (ap-south-1)**, connected manually. Do not propose moving the region. Keep the Email provider **on** with only "Confirm email" off (else login fails with `email_provider_disabled`).
- **Migrations** only as SQL in `supabase/migrations/*.sql`, applied with `scripts/migrate.py`. Never change the schema by hand in the dashboard.
- **Auth**: web uses `@supabase/ssr` with `web/proxy.ts` (`getClaims()` refreshes sessions; never trust `getSession()` on the server). API verifies the JWT against JWKS; `sub` is the user ID. Roles live only in `memberships` or `app_metadata`, never `user_metadata`.
- **Small-merchant accounts (2026-11-24)**: the SME API rejects tokens whose `app_metadata.service` is `sosang` (403, `api/bizdna_api/auth.py`). `public.handle_new_user()` sends `@users.sosang.invalid` accounts to `sosang.profiles`/`sosang.consents` only (migration `20261124000000_sosang_auth.sql`).
- **Username login (must hold)**: username + password only; no email input, verification, or mail-based reset. Username → `{username}@users.bizdna.invalid`. Rule (lowercase start; lowercase/digits/underscore; 4–20) and domain are duplicated in `api/bizdna_api/signup.py` and `web/lib/auth.ts`; change both. Sign-up goes through `POST /api/auth/signup` (admin API, `email_confirm: true`), then `signInWithPassword`. 3 required consents (privacy, storage, statistical use), `TERMS_VERSION = 2026-11-18-draft`.
- **Vercel**: project `21111/mbti-for-enterprise`, production https://mbti-for-enterprise-21111.vercel.app, push to `main` auto-deploys. Root `vercel.json` `services`: `/api/(.*)` → api, `/(.*)` → web. Check previews with `vercel curl` (`MSYS_NO_PATHCONV=1` in Git Bash). `vercel env rm` needs human approval; use `vercel env update` to change a value.

## 12. Manager-tendency data collection (analytics store) — full text in `docs/analytics-store.md`

Implemented and applied to production on 2026-11-18. Subsections 12.1–12.13 (purpose, decisions, principles, DNA direction values, whitelist, migration SQL, collection flow, aggregates, access, open items, deviations) live in `docs/analytics-store.md` with the same numbers; code comments citing "CLAUDE.md 12.x" refer there. Read it before changing `analytics.py`, `store.py` collection, `admin.py`, or the analytics migration. Must-hold rules:

- Source (`public.diagnoses`) and analytics are separate; analytics rows are derived by the pure function `derive_rows` **in the same transaction** as the final save, only for members with statistical-use consent. No guests, no drafts.
- **Whitelist extraction only** (12.5). Never company name, free text, or member ID; people are linked only by `subject_key` (`private.subject_map`).
- DNA stored as 4 axis **direction values** `(score − 50) × 2`; letters and boundary are derived at read time from that row's model-version cut-offs. Item-level answers are not stored.
- `analytics` and `private` are not exposed to the Data API (RLS on, privileges revoked). Never mix model versions in one aggregate. Non-admin aggregates hide cells with `n < k` (k = 5, hypothesis) in the API.
- Rows remain after round/account deletion (only `subject_map` is removed). Admin views/exports are audit-logged (`docs/admin.md`).
- Dummy data: `scripts/seed_dummy.py` loaded 100 rounds into production (2026-11-18); remove with `--clean` before real operation.

## 13. Small-merchant diagnosis (`sosang/`)

- `sosang/` holds the **small-merchant (소상공인) diagnosis**, a separate product developed inside this repo since 2026-11-23 (user decision). It shares this repo, the Supabase project, and the Vercel project, but **member accounts are separate** from Biz-DNA SME accounts. It will later be served on the same URL as this site.
- **`sosang/CLAUDE.md` governs work under `sosang/`** (its docs are Korean; its items, DNA axes, types, and strategies differ from this project — never mix them). This file's rules apply to the SME product only.
- Shared-resource rules that affect this project: small-merchant tables live in `sosang*` schemas; small-merchant routes use `/sosang/*` and `/api/sosang/*`; small-merchant accounts use `@users.sosang.invalid` and `app_metadata.service = "sosang"`. Before small-merchant sign-up opens, `public.handle_new_user()` and this project's API must stop treating small-merchant accounts as SME members (`sosang/CLAUDE.md` 3.4). Changes to this project's code, migrations, or production need user confirmation.
