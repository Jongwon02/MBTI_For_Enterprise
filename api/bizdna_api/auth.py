"""FR-01 로그인 확인. 웹이 보낸 Supabase access token(Authorization: Bearer)을 검증한다.

- 새 Supabase 프로젝트: 비대칭 서명 키 → {SUPABASE_URL}/auth/v1/.well-known/jwks.json 로 검증(키는 메모리에 캐시,
  모르는 kid가 오면 PyJWKClient가 다시 받는다).
- 구형 프로젝트: HS256 → SUPABASE_JWT_SECRET 으로 검증.
검증한 `sub`가 사용자 ID다. 역할·권한은 user_metadata가 아니라 DB 기준으로 판단한다(CLAUDE.md 11.3).
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import jwt
from fastapi import Header, HTTPException

from . import settings


SOSANG_SERVICE = "sosang"


@dataclass(frozen=True)
class User:
    id: str
    email: str | None


@lru_cache(maxsize=4)
def _jwks_client(url: str) -> jwt.PyJWKClient:
    return jwt.PyJWKClient(f"{url}/auth/v1/.well-known/jwks.json", cache_keys=True, lifespan=3600)


def verify_token(token: str) -> User:
    try:
        alg = jwt.get_unverified_header(token).get("alg")
        if alg not in ("HS256", "RS256", "ES256"):
            raise jwt.InvalidTokenError(f"허용하지 않는 서명 방식: {alg}")
        if alg == "HS256":
            if not settings.SUPABASE_JWT_SECRET:
                raise jwt.InvalidTokenError("HS256 비밀값이 설정되지 않았습니다.")
            key: object = settings.SUPABASE_JWT_SECRET
        else:
            if not settings.SUPABASE_URL:
                raise jwt.InvalidTokenError("SUPABASE_URL이 설정되지 않았습니다.")
            key = _jwks_client(settings.SUPABASE_URL).get_signing_key_from_jwt(token).key
        claims = jwt.decode(token, key, algorithms=[alg], audience="authenticated",
                            options={"require": ["sub", "exp"]})
    except (jwt.PyJWTError, ValueError) as e:
        raise HTTPException(status_code=401, detail="로그인이 만료되었거나 올바르지 않습니다. 다시 로그인하세요.") from e
    if claims.get("role") != "authenticated":
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    # 같은 Supabase Auth를 쓰는 소상공인 진단 계정(sosang/CLAUDE.md 3.4)은 이 서비스에 들어올 수 없다.
    if (claims.get("app_metadata") or {}).get("service") == SOSANG_SERVICE:
        raise HTTPException(status_code=403, detail="소상공인 진단 계정입니다. 중소기업 진단은 별도 회원가입이 필요합니다.")
    return User(id=str(claims["sub"]), email=claims.get("email"))


def current_user(authorization: str | None = Header(default=None)) -> User:
    """로그인이 필요한 API의 의존성."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    return verify_token(authorization.split(" ", 1)[1].strip())
