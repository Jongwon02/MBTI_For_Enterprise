"""관리자 계정 만들기·권한 주기(docs/admin.md). 관리자는 웹에서 스스로 가입할 수 없고 이 스크립트로만 만든다.

실행 (저장소 루트에서):
  .venv/Scripts/python scripts/grant_admin.py <아이디>            # 계정이 있으면 관리자 권한만 준다
  .venv/Scripts/python scripts/grant_admin.py <아이디> --create   # 없으면 만든다. 비밀번호는 입력받는다
  .venv/Scripts/python scripts/grant_admin.py <아이디> --revoke   # 관리자 권한을 회수한다(계정은 남김)

비밀번호는 명령줄 인자로 받지 않는다(셸 기록에 남지 않게). 환경변수 BIZDNA_ADMIN_PASSWORD가 있으면 그 값을,
없으면 화면에서 입력받는다. 연결: api/.env의 SUPABASE_URL·SUPABASE_SECRET_KEY·POSTGRES_URL_NON_POOLING.
"""
from __future__ import annotations

import argparse
import getpass
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "api"))

import psycopg  # noqa: E402

from bizdna_api import settings  # noqa: E402
from bizdna_api.signup import MIN_PASSWORD, USERNAME_RE, username_to_email  # noqa: E402
from bizdna_api.store import _clean_url  # noqa: E402


def _admin_api(method: str, path: str, body: dict | None = None) -> dict:
    key = settings.SUPABASE_SECRET_KEY
    headers = {"apikey": key, "Content-Type": "application/json"}
    if key.startswith("eyJ"):
        headers["Authorization"] = f"Bearer {key}"
    req = urllib.request.Request(f"{settings.SUPABASE_URL}/auth/v1/admin/{path}", method=method, headers=headers,
                                 data=json.dumps(body).encode() if body is not None else None)
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            return json.loads(res.read() or b"{}")
    except urllib.error.HTTPError as e:
        raise SystemExit(f"Supabase 관리자 API 오류 {e.code}: {e.read().decode(errors='replace')[:200]}") from e


def main() -> int:
    ap = argparse.ArgumentParser(description="관리자 계정 만들기·권한 주기")
    ap.add_argument("username")
    ap.add_argument("--create", action="store_true", help="계정이 없으면 만든다")
    ap.add_argument("--revoke", action="store_true", help="관리자 권한을 회수한다")
    args = ap.parse_args()

    if not (settings.SUPABASE_URL and settings.SUPABASE_SECRET_KEY and settings.POSTGRES_URL_NON_POOLING):
        print("api/.env에 SUPABASE_URL, SUPABASE_SECRET_KEY, POSTGRES_URL_NON_POOLING이 필요합니다.")
        return 1
    username = args.username.strip().lower()
    if not USERNAME_RE.match(username):
        print("아이디는 영문 소문자로 시작하는 4~20자(영문 소문자·숫자·밑줄)여야 합니다.")
        return 1
    email = username_to_email(username)

    with psycopg.connect(_clean_url(settings.POSTGRES_URL_NON_POOLING), autocommit=True) as c:
        row = c.execute("select id from auth.users where email = %s", (email,)).fetchone()
        if args.revoke:
            if row:
                c.execute("delete from public.memberships where user_id = %s and role = 'admin'", (row[0],))
            print(f"관리자 권한 회수: {username}")
            return 0
        if not row:
            if not args.create:
                print(f"'{username}' 계정이 없습니다. 만들려면 --create를 붙이세요.")
                return 1
            password = os.environ.get("BIZDNA_ADMIN_PASSWORD") or getpass.getpass("비밀번호: ")
            if len(password) < MIN_PASSWORD:
                print(f"비밀번호는 {MIN_PASSWORD}자 이상이어야 합니다.")
                return 1
            # 관리자 계정은 진단 동의(consents)를 받지 않는다. 관리자 계정으로 한 진단은 수집되지 않는다.
            user = _admin_api("POST", "users", {"email": email, "password": password, "email_confirm": True,
                                                "user_metadata": {"name": "관리자", "username": username}})
            user_id = user["id"]
            print(f"계정 생성: {username}")
        else:
            user_id = row[0]
        c.execute("insert into public.memberships (user_id, role) values (%s, 'admin') on conflict do nothing",
                  (user_id,))
    print(f"관리자 권한 부여: {username}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
