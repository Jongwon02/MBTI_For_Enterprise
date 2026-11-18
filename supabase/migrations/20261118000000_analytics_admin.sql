-- 경영자 성향 데이터 수집(CLAUDE.md 12장)과 관리자 계정·조회 기록(docs/admin.md).
-- 분석 스키마(analytics)와 가명키 대응표(private)는 Data API에 노출하지 않는다. FastAPI 서버 연결만 쓴다.
-- 2026-11-18 결정: 통계 활용 동의는 가입 필수 동의에 포함, 회원·회차를 삭제해도 분석 행은 남긴다(가명 상태).

-- 1. 스키마와 권한 -------------------------------------------------------------
create schema if not exists private;
create schema if not exists analytics;
revoke all on schema private, analytics from public, anon, authenticated;
alter default privileges in schema private, analytics revoke all on tables from public, anon, authenticated;
alter default privileges in schema private, analytics revoke all on functions from public, anon, authenticated;

-- 2. 통계 활용 동의 종류 추가 ----------------------------------------------------
alter table public.consents drop constraint if exists consents_kind_check;
alter table public.consents add constraint consents_kind_check
  check (kind in ('privacy', 'storage', 'ai', 'analytics'));

-- 가입 트리거가 analytics 동의도 consents로 옮기게 한다(나머지는 20261117000000과 같음).
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
declare
  c record;
begin
  insert into public.profiles (id, name)
  values (new.id, nullif(new.raw_user_meta_data ->> 'name', ''))
  on conflict (id) do nothing;

  if jsonb_typeof(new.raw_user_meta_data -> 'consents') = 'object' then
    for c in select key, value from jsonb_each_text(new.raw_user_meta_data -> 'consents') loop
      if c.key in ('privacy', 'storage', 'ai', 'analytics') then
        insert into public.consents (user_id, kind, terms_version) values (new.id, c.key, c.value);
      end if;
    end loop;
  end if;
  return new;
end;
$$;

-- 3. 역할 (CLAUDE.md 11.4 memberships의 첫 구현: 지금은 admin만 쓴다) -------------------
-- 사용자가 고칠 수 없는 곳(DB)에 역할을 둔다. user_metadata는 권한 판단에 쓰지 않는다.
create table if not exists public.memberships (
  user_id         uuid not null references auth.users (id) on delete cascade,
  role            text not null check (role in ('company', 'consultant', 'agency', 'admin')),
  organization_id uuid,
  created_at      timestamptz not null default now(),
  primary key (user_id, role)
);
alter table public.memberships enable row level security;
drop policy if exists "memberships_select_own" on public.memberships;
create policy "memberships_select_own" on public.memberships for select to authenticated using ((select auth.uid()) = user_id);
revoke insert, update, delete on public.memberships from anon, authenticated;

-- 4. 가명키 대응표. 회원이 탈퇴하면 이 행만 지워지고 분석 행은 누구 것인지 알 수 없는 상태로 남는다 ----
create table if not exists private.subject_map (
  user_id     uuid primary key references auth.users (id) on delete cascade,
  subject_key uuid not null unique default gen_random_uuid(),
  created_at  timestamptz not null default now()
);

-- 5. 진단 회차 팩트 (회차 × 모형 버전 1행). diagnosis_id에 FK를 두지 않는다: 원본 회차를 지워도 남긴다 ----
create table if not exists analytics.diagnosis_facts (
  fact_id            uuid primary key default gen_random_uuid(),
  diagnosis_id       uuid not null,
  model_version      text not null,
  questions_version  text not null,
  subject_key        uuid not null,
  round_no           int  not null check (round_no >= 1),
  phase              text not null check (phase in ('basic', 'full')),
  completed_at       timestamptz not null,
  -- 기업정보 (원값)
  industry           text,
  founded_year       int,
  sales_recent       numeric,
  sales_prev         numeric,
  operating_margin   numeric,
  employees          int,
  customer_type      text[],
  -- 경영자 성향 (12.4 방향값)
  dna_type           text,
  dna_g_dir          numeric(5,2) check (dna_g_dir between -100 and 100),
  dna_i_dir          numeric(5,2) check (dna_i_dir between -100 and 100),
  dna_n_dir          numeric(5,2) check (dna_n_dir between -100 and 100),
  dna_p_dir          numeric(5,2) check (dna_p_dir between -100 and 100),
  dna_g_answered     smallint not null default 0,
  dna_i_answered     smallint not null default 0,
  dna_n_answered     smallint not null default 0,
  dna_p_answered     smallint not null default 0,
  -- 성장단계 (원값)
  stage_product      smallint, stage_customer smallint, stage_revenue smallint,
  stage_cash         smallint, stage_operations smallint, stage_expansion smallint,
  stage_code         text,
  stage_weighted_index numeric,
  stage_provisional  text,
  stage_gate_adjusted boolean,
  stage_gates        text[],
  -- 역량 요약 (정밀진단만)
  total_score        numeric,
  grade              text,
  competence_missing_ratio numeric,
  -- 성장계획·제약 (원값)
  goals              text[],
  risk_flags         text[],
  plan               jsonb,
  created_at         timestamptz not null default now(),
  updated_at         timestamptz not null default now(),
  unique (diagnosis_id, model_version)
);

create table if not exists analytics.domain_scores (
  fact_id  uuid not null references analytics.diagnosis_facts (fact_id) on delete cascade,
  domain   char(1) not null check (domain in ('A','B','C','D','E','F','G','H')),
  score    numeric,
  weight   numeric not null,
  answered smallint not null,
  primary key (fact_id, domain)
);

create table if not exists analytics.strategy_scores (
  fact_id     uuid not null references analytics.diagnosis_facts (fact_id) on delete cascade,
  strategy    text not null,
  fit         numeric, urgency numeric, impact numeric, feasibility numeric,
  total       numeric not null,
  rank        smallint not null,
  status      text not null check (status in ('recommended', 'deferred')),
  rule_ids    text[] not null default '{}',
  primary key (fact_id, strategy)
);

-- 진행 이벤트. 같은 회차의 같은 이벤트는 한 번만 센다(재저장해도 중복되지 않게).
create table if not exists analytics.funnel_events (
  id           bigint generated always as identity primary key,
  subject_key  uuid not null,
  diagnosis_id uuid not null,
  event        text not null check (event in ('started', 'basic_completed', 'full_completed', 'report_downloaded')),
  occurred_at  timestamptz not null default now(),
  unique (diagnosis_id, event)
);

-- 6. 관리자 조회·내보내기 기록 ------------------------------------------------------
create table if not exists private.audit_logs (
  id        bigint generated always as identity primary key,
  actor_id  uuid not null,
  action    text not null,
  detail    jsonb not null default '{}'::jsonb,
  at        timestamptz not null default now()
);

-- 7. RLS (정책 없음 = Data API 직접 접근 차단) --------------------------------------
alter table private.subject_map        enable row level security;
alter table private.audit_logs         enable row level security;
alter table analytics.diagnosis_facts  enable row level security;
alter table analytics.domain_scores    enable row level security;
alter table analytics.strategy_scores  enable row level security;
alter table analytics.funnel_events    enable row level security;

-- 8. 인덱스 ---------------------------------------------------------------------
create index if not exists diagnosis_facts_industry_stage_idx on analytics.diagnosis_facts (industry, stage_code);
create index if not exists diagnosis_facts_dna_type_idx on analytics.diagnosis_facts (dna_type);
create index if not exists diagnosis_facts_subject_idx on analytics.diagnosis_facts (subject_key, round_no);
create index if not exists diagnosis_facts_model_idx on analytics.diagnosis_facts (model_version, completed_at desc);
create index if not exists funnel_events_subject_idx on analytics.funnel_events (subject_key, event);
create index if not exists audit_logs_at_idx on private.audit_logs (at desc);

-- 9. 가명키 발급 (없으면 만들고, 있으면 그대로 돌려준다) ---------------------------------
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
