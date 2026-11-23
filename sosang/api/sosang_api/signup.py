"""소상공인 회원가입: 아이디 + 비밀번호, 이메일 인증 없음(중소경영과 같은 방식, sosang/CLAUDE.md 3.4).

- 아이디는 내부용 주소 `{아이디}@users.sosang.invalid`로 바꿔 넣는다(중소경영은 @users.bizdna.invalid).
  그래서 같은 아이디를 두 서비스에서 따로 가입할 수 있다. 웹(`web/lib/auth.ts`)도 같은 규칙으로 로그인하므로 함께 고친다.
- Supabase 관리자 API로 이메일 확인이 끝난 계정을 만들고 `app_metadata.service = "sosang"`을 넣는다.
  API 권한은 이 값으로 판단한다(`user_metadata`는 사용자가 바꿀 수 있어 쓰지 않는다).
- 가입 트리거(public.handle_new_user, 20261124000000_sosang_auth.sql)가 주소 도메인을 보고
  sosang.profiles·sosang.consents에 행을 만든다. 중소경영 public.* 에는 쓰지 않는다.
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
from .auth import SERVICE

USERNAME_RE = re.compile(r"^[a-z][a-z0-9_]{3,19}$")
LOGIN_DOMAIN = "users.sosang.invalid"
MIN_PASSWORD = 8


class SignupRequest(BaseModel):
    username: str = Field(max_length=40)
    password: str = Field(max_length=72)  # bcrypt 한도
    name: str = Field(default="", max_length=40)
    agree_privacy: bool = False
    agree_storage: bool = False
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
    if not (req.agree_privacy and req.agree_storage):
        raise HTTPException(status_code=422, detail="필수 동의 항목에 동의해야 가입할 수 있습니다.")

    status, body = _admin_create_user({
        "email": username_to_email(username),
        "password": req.password,
        "email_confirm": True,  # 이메일 인증 없이 바로 사용
        "app_metadata": {"service": SERVICE},
        "user_metadata": {
            "name": req.name.strip(),
            "username": username,
            "consents": {"privacy": req.terms_version, "storage": req.terms_version},
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
