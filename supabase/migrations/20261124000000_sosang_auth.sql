-- 소상공인 회원가입·로그인과 진단 저장 (sosang/CLAUDE.md 3.3·3.4·11.1).
-- 같은 Supabase 프로젝트를 중소경영과 같이 쓰되, 소상공인 데이터는 모두 sosang 스키마에 둔다.
-- 브라우저는 Supabase를 로그인에만 쓰고 테이블은 소상공인 FastAPI가 서버 전용 연결로 읽고 쓴다.
-- sosang 스키마는 Data API에 노출하지 않는다(권한 회수 + RLS). 중소경영 객체는 handle_new_user()만 고친다.

create schema if not exists sosang;
revoke all on schema sosang from public, anon, authenticated;

-- 1. 회원 프로필 ---------------------------------------------------------------
create table if not exists sosang.profiles (
  id         uuid primary key references auth.users (id) on delete cascade,
  name       text,
  username   text,
  created_at timestamptz not null default now()
);
alter table sosang.profiles enable row level security;

-- 2. 동의 기록 (개인정보 수집·이용, 진단결과 저장, 통계 활용, AI 분석) --------------------
create table if not exists sosang.consents (
  id            bigint generated always as identity primary key,
  user_id       uuid not null references auth.users (id) on delete cascade,
  kind          text not null check (kind in ('privacy', 'storage', 'analytics', 'ai')),
  terms_version text not null,
  agreed_at     timestamptz not null default now(),
  withdrawn_at  timestamptz
);
create index if not exists sosang_consents_user_idx on sosang.consents (user_id);
alter table sosang.consents enable row level security;

-- 3. 진단 회차. status: draft(진행 중·중간저장) → completed(최종저장, 엔진 결과와 버전 함께 저장) --------
-- 점포 마스터(stores)·재무 기록(financial_records)은 아직 만들지 않는다. 점포·재무 입력은 survey(jsonb)에 들어 있다.
create table if not exists sosang.assessments (
  id                 uuid primary key default gen_random_uuid(),
  created_by         uuid not null references auth.users (id) on delete cascade,
  store_name         text,
  status             text not null default 'draft' check (status in ('draft', 'completed')),
  survey             jsonb not null default '{}'::jsonb,
  progress           jsonb not null default '{}'::jsonb,
  result             jsonb,
  model_version      text,
  questions_version  text,
  industries_version text,
  created_at         timestamptz not null default now(),
  updated_at         timestamptz not null default now(),
  completed_at       timestamptz
);
create index if not exists sosang_assessments_owner_idx on sosang.assessments (created_by, updated_at desc);
alter table sosang.assessments enable row level security;

-- Data API(anon·authenticated)로는 읽기·쓰기 모두 막는다. FastAPI(서버 전용 연결)만 쓴다.
revoke all on all tables in schema sosang from public, anon, authenticated;
alter default privileges in schema sosang revoke all on tables from public, anon, authenticated;

-- 4. 가입 트리거를 서비스별로 나눈다 -------------------------------------------------
-- 소상공인 계정(내부 주소 @users.sosang.invalid)은 sosang.profiles·sosang.consents에만 쓰고,
-- 그 밖의 계정은 지금까지처럼 public.profiles·public.consents에 쓴다(20261118000000과 같음).
-- 주소 도메인은 가입 요청(INSERT)과 함께 정해지므로 이것으로 나눈다. API 권한은 app_metadata.service로 따로 확인한다.
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
declare
  c record;
begin
  if lower(coalesce(new.email, '')) like '%@users.sosang.invalid' then
    insert into sosang.profiles (id, name, username)
    values (new.id, nullif(new.raw_user_meta_data ->> 'name', ''), nullif(new.raw_user_meta_data ->> 'username', ''))
    on conflict (id) do nothing;

    if jsonb_typeof(new.raw_user_meta_data -> 'consents') = 'object' then
      for c in select key, value from jsonb_each_text(new.raw_user_meta_data -> 'consents') loop
        if c.key in ('privacy', 'storage', 'analytics', 'ai') then
          insert into sosang.consents (user_id, kind, terms_version) values (new.id, c.key, c.value);
        end if;
      end loop;
    end if;
    return new;
  end if;

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
