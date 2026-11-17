"""FR-01 회원가입(이메일 인증 없음, 2026-11-17 결정).

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

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD = 8


class SignupRequest(BaseModel):
    email: str = Field(max_length=254)
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


def signup(req: SignupRequest) -> dict[str, Any]:
    if not (settings.SUPABASE_URL and settings.SUPABASE_SECRET_KEY):
        raise HTTPException(status_code=503, detail="회원 기능이 아직 설정되지 않았습니다. 게스트로 진단할 수 있습니다.")
    email = req.email.strip().lower()
    if not EMAIL_RE.match(email):
        raise HTTPException(status_code=422, detail="이메일 형식을 확인해 주세요.")
    if len(req.password) < MIN_PASSWORD:
        raise HTTPException(status_code=422, detail=f"비밀번호는 {MIN_PASSWORD}자 이상이어야 합니다.")
    if not (req.agree_privacy and req.agree_storage):
        raise HTTPException(status_code=422, detail="필수 동의 항목에 동의해야 가입할 수 있습니다.")

    status, body = _admin_create_user({
        "email": email,
        "password": req.password,
        "email_confirm": True,  # 이메일 인증 없이 바로 사용
        "user_metadata": {
            "name": req.name.strip(),
            "consents": {"privacy": req.terms_version, "storage": req.terms_version},
        },
    })
    if status in (200, 201):
        return {"id": body.get("id"), "email": email}
    code = str(body.get("error_code") or body.get("code") or "")
    msg = str(body.get("msg") or body.get("message") or "").lower()
    if code == "email_exists" or "already" in msg:
        raise HTTPException(status_code=409, detail="이미 가입된 이메일입니다. 로그인해 주세요.")
    if code == "weak_password" or "password" in msg:
        raise HTTPException(status_code=422, detail="비밀번호가 너무 쉽습니다. 영문·숫자를 섞어 8자 이상으로 정해 주세요.")
    if status == 429:
        raise HTTPException(status_code=429, detail="요청이 너무 많습니다. 잠시 후 다시 시도해 주세요.")
    raise HTTPException(status_code=502, detail="가입을 처리하지 못했습니다. 잠시 후 다시 시도해 주세요.")
