"""환경변수 설정. sosang/api/.env를 읽는다(이미 설정된 환경변수가 우선). 예시는 sosang/api/.env.example."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)


def _get(name: str, default: str) -> str:
    """비어 있는 값(`KEY=`)은 설정하지 않은 것으로 본다."""
    return (os.environ.get(name) or "").strip() or default


ENV = _get("SOSANG_ENV", "development")
IS_PRODUCTION = ENV == "production"

CORS_ORIGINS = [x.strip() for x in _get("SOSANG_CORS_ORIGINS", "http://localhost:3001,http://127.0.0.1:3001").split(",") if x.strip()]

API_DOCS_ENABLED = _get("SOSANG_API_DOCS", "false" if IS_PRODUCTION else "true").lower() == "true"

# ---- Supabase (회원가입·로그인·진단 저장). 중소경영과 같은 프로젝트·같은 변수 이름을 쓴다(sosang/CLAUDE.md 11장). ----
# 비어 있으면 회원 API가 503을 돌려주고 게스트 진단은 그대로 동작한다.
SUPABASE_URL = _get("SUPABASE_URL", _get("NEXT_PUBLIC_SUPABASE_URL", "")).rstrip("/")
# 구형(HS256) 프로젝트의 JWT 비밀값. 새 프로젝트는 비대칭 키(JWKS)로 검증하므로 비워 둬도 된다.
SUPABASE_JWT_SECRET = _get("SUPABASE_JWT_SECRET", "")
# 풀링 연결(트랜잭션 풀러). 서버 전용. 절대 웹 쪽 변수에 두지 않는다.
POSTGRES_URL = _get("POSTGRES_URL", "")
# 관리자 키(가입 처리용). 서버 전용.
SUPABASE_SECRET_KEY = _get("SUPABASE_SECRET_KEY", _get("SUPABASE_SERVICE_ROLE_KEY", ""))
