-- FR-01 회원가입·로그인, FR-12 진단 저장(중간저장·최종저장).
-- 브라우저는 Supabase를 로그인에만 쓰고 테이블은 FastAPI가 서버 전용 연결로 읽고 쓴다(CLAUDE.md 11.1).
-- 그래서 모든 테이블에 RLS를 켜고, 정책은 "본인 것만 조회"로 이중 방어만 둔다.

-- 사용자 프로필 ------------------------------------------------------------
create table if not exists public.profiles (
  id uuid primary key references auth.users (id) on delete cascade,
  name text,
  phone text,
  created_at timestamptz not null default now()
);
alter table public.profiles enable row level security;
drop policy if exists "profiles_select_own" on public.profiles;
create policy "profiles_select_own" on public.profiles for select to authenticated using ((select auth.uid()) = id);

-- 동의 기록 (개인정보 수집·이용, 진단결과 저장, AI 분석) ------------------------
create table if not exists public.consents (
  id bigint generated always as identity primary key,
  user_id uuid not null references auth.users (id) on delete cascade,
  company_id uuid,
  kind text not null check (kind in ('privacy', 'storage', 'ai')),
  terms_version text not null,
  agreed_at timestamptz not null default now(),
  withdrawn_at timestamptz
);
create index if not exists consents_user_idx on public.consents (user_id);
alter table public.consents enable row level security;
drop policy if exists "consents_select_own" on public.consents;
create policy "consents_select_own" on public.consents for select to authenticated using ((select auth.uid()) = user_id);

-- 가입 시 프로필과 동의 기록을 만든다. 동의는 가입 요청의 user_metadata.consents({kind: version})에서 한 번만 옮긴다.
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
      if c.key in ('privacy', 'storage', 'ai') then
        insert into public.consents (user_id, kind, terms_version) values (new.id, c.key, c.value);
      end if;
    end loop;
  end if;
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

-- 진단 회차 ----------------------------------------------------------------
-- status: draft(진행 중·중간저장) → basic_completed(기본진단 최종저장) → full_completed(정밀진단 최종저장)
-- company_id는 기업 등록(companies, 11.4)이 생기면 연결한다. 그전까지는 작성자(created_by) 기준으로 권한을 판단한다.
create table if not exists public.diagnoses (
  id uuid primary key default gen_random_uuid(),
  created_by uuid not null references auth.users (id) on delete cascade,
  company_id uuid,
  company_name text,
  phase text not null default 'basic' check (phase in ('basic', 'full')),
  status text not null default 'draft' check (status in ('draft', 'basic_completed', 'full_completed')),
  survey jsonb not null default '{}'::jsonb,
  progress jsonb not null default '{}'::jsonb,
  result jsonb,
  model_version text,
  questions_version text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  completed_at timestamptz
);
create index if not exists diagnoses_owner_idx on public.diagnoses (created_by, updated_at desc);
alter table public.diagnoses enable row level security;
drop policy if exists "diagnoses_select_own" on public.diagnoses;
create policy "diagnoses_select_own" on public.diagnoses for select to authenticated using ((select auth.uid()) = created_by);

-- Data API(공개 키)로는 쓰기를 열지 않는다. 쓰기는 FastAPI만 한다.
revoke insert, update, delete on public.profiles, public.consents, public.diagnoses from anon, authenticated;
