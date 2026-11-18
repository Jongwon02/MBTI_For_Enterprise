"""FR-01 회원가입: 아이디 + 비밀번호, 이메일 인증 없음(2026-11-17·18 결정).

Supabase Auth는 이메일(또는 휴대폰)로만 계정을 만들 수 있어, 아이디를 내부용 주소
`{아이디}@users.bizdna.invalid`로 바꿔 넣는다(.invalid는 메일이 가지 않는 예약 도메인).
웹(`web/lib/auth.ts`의 `usernameToEmail`)도 같은 규칙으로 로그인하므로 둘을 함께 고친다.
Supabase 관리자 API로 이메일 확인이 끝난 계정을 바로 만든다. 그래서 대시보드의 "Confirm email" 설정과
상관없이 가입 직후 로그인할 수 있다. 관리자 키(SUPABASE_SECRET_KEY)는 이 서버에서만 쓴다.
가입 트리거(supabase/migrations)가 user_metadata의 name·consents로 profiles·consents 행을 만든다.
"""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from typing import Any

from fastapi import HTTPException
from pydantic import BaseModel, Field

from . import settings

# 아이디: 영문 소문자로 시작, 영문 소문자·숫자·밑줄 4~20자. 대문자로 입력해도 소문자로 바꾼다.
USERNAME_RE = re.compile(r"^[a-z][a-z0-9_]{3,19}$")
LOGIN_DOMAIN = "users.bizdna.invalid"
MIN_PASSWORD = 8


class SignupRequest(BaseModel):
    username: str = Field(max_length=40)
    password: str = Field(max_length=72)  # bcrypt 한도
    name: str = Field(default="", max_length=40)
    agree_privacy: bool = False
    agree_storage: bool = False
    agree_analytics: bool = False  # 통계 활용 동의. 2026-11-18 결정으로 가입 필수 동의에 포함한다(CLAUDE.md 12.2)
    terms_version: str = Field(max_length=40)


def _admin_create_user(payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    """POST {SUPABASE_URL}/auth/v1/admin/users. (상태코드, 본문)을 돌려준다. 테스트는 이 함수를 바꿔 끼운다."""
    key = settings.SUPABASE_SECRET_KEY
    headers = {"apikey": key, "Content-Type": "application/json"}
    if key.startswith("eyJ"):  # 구형 service_role JWT는 Authorization 헤더도 필요하다
        headers["Authorization"] = f"Bearer {key}"
    req = urllib.request.Request(f"{settings.SUPABASE_URL}/auth/v1/admin/users", data=json.dumps(payload).encode(),
                                 headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            return res.status, json.loads(res.read() or b"{}")
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read() or b"{}")
        except ValueError:
            body = {}
        return e.code, body


def username_to_email(username: str) -> str:
    """로그인용 내부 주소. 웹의 usernameToEmail과 같아야 한다."""
    return f"{username}@{LOGIN_DOMAIN}"


def signup(req: SignupRequest) -> dict[str, Any]:
    if not (settings.SUPABASE_URL and settings.SUPABASE_SECRET_KEY):
        raise HTTPException(status_code=503, detail="회원 기능이 아직 설정되지 않았습니다. 게스트로 진단할 수 있습니다.")
    username = req.username.strip().lower()
    if not USERNAME_RE.match(username):
        raise HTTPException(status_code=422, detail="아이디는 영문 소문자로 시작하는 4~20자(영문 소문자·숫자·밑줄)로 정해 주세요.")
    if len(req.password) < MIN_PASSWORD:
        raise HTTPException(status_code=422, detail=f"비밀번호는 {MIN_PASSWORD}자 이상이어야 합니다.")
    if not (req.agree_privacy and req.agree_storage and req.agree_analytics):
        raise HTTPException(status_code=422, detail="필수 동의 항목에 동의해야 가입할 수 있습니다.")

    status, body = _admin_create_user({
        "email": username_to_email(username),
        "password": req.password,
        "email_confirm": True,  # 이메일 인증 없이 바로 사용
        "user_metadata": {
            "name": req.name.strip(),
            "username": username,
            "consents": {"privacy": req.terms_version, "storage": req.terms_version,
                         "analytics": req.terms_version},
        },
    })
    if status in (200, 201):
        return {"id": body.get("id"), "username": username}
    code = str(body.get("error_code") or body.get("code") or "")
    msg = str(body.get("msg") or body.get("message") or "").lower()
    if code == "email_exists" or "already" in msg:
        raise HTTPException(status_code=409, detail="이미 사용 중인 아이디입니다. 다른 아이디를 정해 주세요.")
    if code == "weak_password" or "password" in msg:
        raise HTTPException(status_code=422, detail="비밀번호가 너무 쉽습니다. 영문·숫자를 섞어 8자 이상으로 정해 주세요.")
    if status == 429:
        raise HTTPException(status_code=429, detail="요청이 너무 많습니다. 잠시 후 다시 시도해 주세요.")
    raise HTTPException(status_code=502, detail="가입을 처리하지 못했습니다. 잠시 후 다시 시도해 주세요.")
