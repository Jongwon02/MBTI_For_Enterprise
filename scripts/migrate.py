"""supabase/migrations/*.sql을 순서대로 DB에 적용한다(Supabase CLI가 없을 때용).

실행: .venv/Scripts/python scripts/migrate.py
연결: POSTGRES_URL_NON_POOLING (api/.env 또는 환경변수). 적용 기록은 Supabase CLI와 같은
supabase_migrations.schema_migrations 테이블에 남기므로 나중에 CLI로 바꿔도 이어서 쓸 수 있다.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "api"))

import psycopg  # noqa: E402

from bizdna_api import settings  # noqa: E402
from bizdna_api.store import _clean_url  # noqa: E402


def main() -> int:
    url = settings.POSTGRES_URL_NON_POOLING
    if not url:
        print("POSTGRES_URL_NON_POOLING이 없습니다. vercel env pull 로 api/.env를 채우세요.")
        return 1
    files = sorted((ROOT / "supabase" / "migrations").glob("*.sql"))
    with psycopg.connect(_clean_url(url), autocommit=True) as c:
        c.execute("create schema if not exists supabase_migrations")
        c.execute("create table if not exists supabase_migrations.schema_migrations"
                  " (version text primary key, statements text[], name text)")
        done = {r[0] for r in c.execute("select version from supabase_migrations.schema_migrations")}
        for f in files:
            version, _, name = f.stem.partition("_")
            if version in done:
                print(f"건너뜀  {f.name}")
                continue
            sql = f.read_text(encoding="utf-8")
            with c.transaction():
                c.execute(sql)
                c.execute("insert into supabase_migrations.schema_migrations (version, statements, name)"
                          " values (%s, %s, %s)", (version, [sql], name))
            print(f"적용함  {f.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
