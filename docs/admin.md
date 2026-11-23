# Admin accounts and manager-data explorer

> Implemented 2026-11-18. The collection design is authoritative in `docs/analytics-store.md` (moved from `CLAUDE.md` section 12). This document covers creating admin accounts, using the screen, and implementation details.

## 1. At a glance

| Item | Details |
| --- | --- |
| Screen | `/admin` (an admin who is logged in sees a **관리자** link at the top right) |
| Admin account | Username `whoami` (created 2026-11-18). The password is never stored in the repo |
| Data shown | The analytics store (`analytics.*`): **final-saved rounds** of members who gave statistical-use consent, pseudonymized |
| Never shown | Company name, representative name, username, contact details, free text, source round ID. They are not stored in the analytics store at all |
| Live refresh | While open, the screen reloads every 15 seconds (only when the tab is visible). Uncheck "실시간 갱신" to stop; "새로고침" refreshes immediately |
| Audit | Every aggregate/list/detail view and CSV export is written to `private.audit_logs` (who, when, which filters, how many rows). Repeated aggregate/list views with identical conditions (e.g. the 15 s auto refresh) are logged once per 10 minutes (`AUDIT_DEDUPE_SECONDS`); detail views and CSV exports are logged every time |

## 2. Creating and revoking admins

Admins cannot sign up on the web. The permission lives in the DB table `public.memberships` (`role = 'admin'`); user-editable `user_metadata` is never used. The API re-checks this table **on every request**.

Run from the repo root. Requires `SUPABASE_URL`, `SUPABASE_SECRET_KEY`, `POSTGRES_URL_NON_POOLING` in `api/.env`.

```bash
# Create a new admin username (password is prompted; never passed as a CLI argument)
.venv/Scripts/python scripts/grant_admin.py <username> --create

# Grant admin to an existing member
.venv/Scripts/python scripts/grant_admin.py <username>

# Revoke admin (the account remains)
.venv/Scripts/python scripts/grant_admin.py <username> --revoke
```

- Instead of the prompt, the password can come from the env var `BIZDNA_ADMIN_PASSWORD` (automation).
- To change an admin password: Supabase dashboard Authentication → Users, select the account (`<username>@users.bizdna.invalid`), set a new password; or call the admin API `PUT /auth/v1/admin/users/{id}` with the secret key. There is no mail-based reset (CLAUDE.md 11.3). The `whoami` password was changed on 2026-11-18.
- Admin accounts have no statistical-use consent, so diagnoses made with an admin account are not collected.

## 3. Screen layout

1. **Filters (one row)**: industry, phase (basic/full), growth stage, DNA type, period (by completion date, end date inclusive). Changing them updates aggregates and the list together.
2. **Summary**: round count, manager count (by pseudonymous key), full-diagnosis ratio, median total competence, funnel (start → basic done → full done; whole period, independent of filters).
3. **Manager tendency, 4 axes**: mean direction value per axis (−100 to +100) as bars diverging from the center. Blue = A tendency (G, I, N, P), orange = B tendency (S, E, C, O); the gray band in the middle is the boundary zone (direction −20 to +20 = axis score 40–60). A-tendency share, boundary share, and sample size are shown alongside.
4. **Distribution charts**: DNA type, growth stage, industry, rank 1–3 recommended strategies, growth obstacles (P09), growth goals (P01). Hovering a bar shows count and share.
5. **8-competence score distribution** (full diagnosis only): p25–p75 band and median per domain.
6. **Round list**: 25 per page. Completion date, first 8 chars of the pseudonymous key, round number (which completed round of that manager), raw company values (industry, founding year, revenue, headcount), DNA type and 4 direction values, stage, total score and grade, top 3 strategies. Clicking a row opens the **detail** (6 stage indicators, 8 domain scores, 12 strategy scores with deferral rules, goals and obstacles, raw P answers).
7. **CSV export**: the full round list for the current filters (max 20,000 rows), with a UTF-8 BOM so Excel opens it correctly.

Chart colors: single series uses accent blue `#0071e3`; axis directions use blue `#0071e3` / orange `#c2410c`. This pair passed the color-vision-deficiency check (CVD ΔE ≥ 30). Values are never encoded by color alone; letters (G/S etc.) and numbers are always shown.

## 4. API

All endpoints require `Authorization: Bearer <Supabase access token>` and return 403 for non-admins.

| Method and path | Content |
| --- | --- |
| `GET /api/me` | Includes `is_admin`. Used only to decide whether to show the admin link |
| `GET /api/admin/overview` | Aggregates (summary, 4 axes, distributions, competence quantiles, funnel, code labels) |
| `GET /api/admin/facts?offset=&limit=` | Round list (max 200 per page) and total count |
| `GET /api/admin/facts/{fact_id}` | Round detail (with 8 domain rows and 12 strategy rows) |
| `GET /api/admin/export.csv` | Round list as CSV |

Common filter query params: `industry`, `phase` (basic, full), `stage` (S1–S5), `dna_type`, `model_version`, `since`, `until` (YYYY-MM-DD, `until` inclusive).

- **`model_version` defaults to the current model version** so aggregates never mix versions (CLAUDE.md 12.8). The screen has a model-version selector; `overview` returns `model_version` (applied), `current_model_version`, and `available_versions` (row count per version).

- Aggregates are computed in the API from up to 20,000 matching rounds (`ADMIN_ROW_LIMIT`, `summarize_facts` in `api/bizdna_api/analytics.py`). Expected total volume is about 5,000 rounds (2026-11-23), so moving to DB aggregate views is not planned. If the limit is hit, `overview` and `facts` return `truncated: true` and the screen shows a warning (only the most recent rounds are reflected).
- Admins are internal users who also see individual rounds, so small-sample (`k`) hiding is not applied; every aggregate shows `n` instead. Aggregates exposed to agencies or companies must hide cells below `k` per 12.8.

## 5. How collection happens (summary)

- When a member **final-saves a basic or full diagnosis**, the same transaction as the source save writes one fact row (overwritten when the same round is saved again), 8 competence rows, and 12 strategy rows.
- Creating a round records `started`; a basic completion records `basic_completed`; a full completion records both `basic_completed` and `full_completed`. Each event is counted once per round.
- Without statistical-use consent (`consents.kind = 'analytics'`) nothing is written. Members who signed up before 2026-11-18 lack this consent and are not collected.
- Analytics rows remain when a member deletes a round or their account (2026-11-18 decision). Account deletion removes only the key map (`private.subject_map`), so rows become unlinkable.
- To fill existing rounds: `.venv/Scripts/python scripts/backfill_analytics.py` (idempotent).

## 6. Verified (2026-11-18)

- Unit and API tests: `api/tests/test_analytics.py` (direction round trip and boundaries, no leakage of non-whitelisted values, missing values), `api/tests/test_admin.py` (no consent → not collected, basic → full is one row, round numbers, rows survive source deletion, non-admin 403, audit log).
- Real DB: migration applied; `analytics` and `private` schemas confirmed unreachable via the Data API (406); collection, screen, detail, and backfill idempotency verified with 3 fictitious accounts / 5 rounds, then all deleted.
- Production: the user confirmed admin login and `/admin` work online (2026-11-18).
- Operational caveat: when a Supabase pooler connection drops mid-transaction, the DB-side transaction can stay open holding locks, and that member's next save hangs. So every API transaction sets `lock_timeout 5s`, `idle_in_transaction_session_timeout 20s`, `statement_timeout 20s` (`_conn` in `store.py`).

## 7. Dummy data (for checking the screen and collection)

`scripts/seed_dummy.py` creates fictitious members (`dummy_` usernames, with statistical-use consent) and diagnoses, and saves them through the real save path. This is not real company data.

```bash
.venv/Scripts/python scripts/seed_dummy.py --count 100   # create (--seed reproduces the same data)
.venv/Scripts/python scripts/seed_dummy.py --clean       # delete all dummy_ members with their diagnoses and analytics rows
```

- Each axis of the manager tendency is skewed to one side; draws landing in the boundary zone (direction −25 to +25) are redrawn, so there are no neutral values. Lean probabilities differ by industry (e.g. services lean G/I/N, retail leans E).
- About 30% of members have a 2nd round (re-diagnosis); 75% complete the full diagnosis.
- 100 rounds (73 members) were loaded into the production DB on 2026-11-18. Remove them with `--clean` before real operation.
