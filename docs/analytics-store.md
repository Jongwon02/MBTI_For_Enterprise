# Manager-tendency data collection (analytics store)

> Moved verbatim from `CLAUDE.md` section 12 on 2026-11-23 to keep CLAUDE.md short. Subsection numbers are unchanged, so references such as "CLAUDE.md 12.x" in code comments point here. `CLAUDE.md` keeps only the must-hold rules; if the two disagree, update both.

> **Implemented and applied to the production DB on 2026-11-18.** Migration `supabase/migrations/20261118000000_analytics_admin.sql`; code `api/bizdna_api/analytics.py`, `store.py`, `admin.py`; backfill `scripts/backfill_analytics.py`. Admin screen and accounts: `docs/admin.md`. Deviations from the design are in 12.13.

## 12.1 Purpose

Turn members' diagnoses into "meaningful information".

| Use | Examples | Basis |
| --- | --- | --- |
| Peer comparison and aggregation | DNA direction distribution, competence quantiles, obstacle/goal/policy-need distributions by industry, size, age, stage | FR-19, PRD section 10 "peer comparison, de-identified aggregation" |
| Change tracking | Changes in type, direction, stage, and scores at re-diagnosis; type stability (test-retest); completion, full-diagnosis conversion, and re-diagnosis rates | FR-16, PRD section 3 usage metrics |
| Model validation (partial) | DNA boundary ratio, growth-stage gate frequency, strategy recommendation/deferral frequency, evidence for re-weighting | PRD section 3 validation metrics |

Item-level reliability (Cronbach's α, item discrimination) cannot be computed from this store because item answers are not stored (12.2). Add them via 12.9 if needed.

## 12.2 Decisions (2026-11-18, confirmed by the user)

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

## 12.3 Principles

1. **Separate source and analytics.** `public.diagnoses` is the service source of truth. Analytics rows are **derived** from it and must be deletable and rebuildable by backfill at any time.
2. **Extract by whitelist only.** Never copy the source (`survey`, `result`) wholesale or build rows by "removing unneeded keys" (blacklist). New engine fields stay out unless whitelisted. In particular `result.company` and `survey.company` contain the company name and free text.
3. **Link people only by pseudonymous key.** Analytics tables have no `auth.users.id`, only `subject_key`. The member ↔ key map lives in a separate `private` schema.
4. **Do not expose analytics schemas.** `analytics` and `private` are not in the Supabase Data API exposed schemas; every table has RLS on (no policies) and `anon`/`authenticated` privileges revoked. Access is only through FastAPI's server connection (same principle as 11.1).
5. **Only consented rounds.** Only final-saved rounds of members with statistical-use consent (`consents.kind = 'analytics'`, not withdrawn) are stored. This consent is required at sign-up (12.2). Stored rows remain after round or account deletion (12.2).
6. **Store versions too.** Every row has `model_version` and `questions_version`. Recomputing old rounds with a new model adds new-version rows instead of overwriting. Aggregations never mix versions.
7. **No guest diagnoses.** Guest answers live only in the browser (section 9 decision).
8. **Raw values stored, exposure only through aggregates.** Raw values such as revenue and founding year can identify a company. Individual rows leave the system only through admin access (audit-logged); screens and reports show only binned aggregates, and cells with fewer than `k` samples (hypothesis 5) are hidden.

## 12.4 DNA direction-value algorithm

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

## 12.5 Whitelist (source → analytics column)

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

## 12.6 DB setup (migration)

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

## 12.7 Collection flow (API)

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

## 12.8 Aggregate views (examples)

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

## 12.9 Access and future additions

- **Admin**: sees all aggregates and individual fact rows (list, detail) on screen and exports CSV (changed by the 2026-11-18 decision). Each view and export is logged in `private.audit_logs`. The admin screen does not apply `k` hiding but shows `n` (`docs/admin.md`).
- **Agency**: sees **aggregates only** for companies in its programs (`program_enrollments`). Build after `memberships` roles for agencies exist.
- **Consultant**: sees assigned companies via the source (`public.diagnoses`) and receives only peer-comparison values from the analytics store.
- **Company representative**: sees only peer comparisons (quantiles, ratios) on their own result screen.
- Never give external analysis tools a DB account. If needed, create a read-only role restricted to `analytics` views.
- **If item-level answers are needed** (pilot α, discrimination): add `analytics.answer_items(fact_id, section, code, value, scored, is_missing)` and fill by backfill. Rounds deleted from the source cannot be recovered.

## 12.10 Open items (confirm with the user before implementing)

- [x] Statistical-use consent: part of the required sign-up consents (2026-11-18). How to obtain it from earlier members is undecided (they are not collected now)
- [x] Analytics rows on round deletion / account deletion: kept (pseudonymous) (2026-11-18). The privacy policy must say so
- [x] Analytics failure fails the diagnosis save: implemented as one transaction (2026-11-18)
- [ ] Column-level encryption of raw financial fields such as revenue and operating margin (decide with sections 9 and 11.4)
- [ ] Final aggregation bins and the small-group threshold `k` (12.8 draft)
- [ ] Whether and how to share pilot raw data with external researchers
- [ ] Aggregate refresh cadence and tool (Vercel Cron vs `pg_cron`)
- [x] Collection function shape, one row per round, DNA direction values, raw values, no item answers (2026-11-18, 12.2)
- [x] DB region: keep Mumbai (ap-south-1) (2026-11-18, 11.2)

## 12.11 Implementation order (recommended)

1. Settle the 12.10 consent and deletion policies first.
2. Write and apply the 12.6 migration; confirm the Data API does not expose it.
3. `analytics.py`: `axis_direction`, `axis_score`, `derive_rows` + unit tests (12.4 required items, basic/full, missing axes/domains, **no non-whitelisted value in rows**: feed company names, free text, and member ID strings and scan the whole output).
4. Upsert in the same transaction in the final-save API. Tests for permissions and missing consent.
5. Fill existing rounds with the backfill script (idempotency test).
6. Aggregate views and admin query API (with `k` handling), then the agency screen (FR-19) and peer comparison on the result screen.

## 12.12 Things to know about the current storage structure

- `public.diagnoses.result` contains the engine output's full `company` (with company name), and `survey.company` also holds the company name and free text. The derivation function must extract only via the 12.5 whitelist.
- `diagnoses.company_id` is still empty. The pseudonymous key is **per member** for now, so a company re-diagnosed by a different representative looks like a different person. When `companies` exists, decide whether to key by company (better for re-diagnosis tracking).

## 12.13 Deviations from the design during implementation (2026-11-18)

- **Migration**: in addition to the 12.6 SQL, it adds `public.memberships` (admin role), `private.audit_logs`, `analytics` consent handling in the sign-up trigger, and `unique (diagnosis_id, event)` on `funnel_events` (re-saving does not add events).
- **Events**: saving a full completion also records `basic_completed` (full implies basic), so "basic done ≥ full done" holds.
- **Raw P answers**: even for whitelisted keys, only values matching the config (`questions_v1.json`) options or number format are kept, so free strings cannot slip in. Industry and customer type values not among the options are dropped too.
- **Transaction protection**: a pooler connection once dropped mid-transaction and left a lock held on the DB side. Every API transaction sets `lock_timeout 5s`, `idle_in_transaction_session_timeout 20s`, `statement_timeout 20s` via `set_config(..., true)`. Competence and strategy rows are inserted in one statement each to reduce round trips.
- **Aggregation location**: instead of the 12.8 DB views, the API reads the matching rows (up to 20,000, `ADMIN_ROW_LIMIT`) and computes with `summarize_facts`. Total volume is expected to stay around 5,000 rounds (2026-11-23 user statement), so views are not planned; hitting the limit returns `truncated` and the admin screen warns. Admin queries default to the current `model_version` (no version mixing), and repeated identical aggregate/list views are audit-logged once per 10 minutes (detail and CSV every time).
- **Dummy data**: `scripts/seed_dummy.py` creates fictitious `dummy_` members with consent and runs them through the real save path. 100 rounds (73 members) were loaded into the production DB on 2026-11-18 for testing; remove them with `--clean` before real operation.
