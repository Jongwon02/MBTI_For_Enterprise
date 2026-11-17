"""환경변수 설정. api/.env를 읽는다(이미 설정된 환경변수가 우선). 예시는 api/.env.example."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)


def _get(name: str, default: str) -> str:
    """비어 있는 값(`KEY=`)은 설정하지 않은 것으로 본다."""
    return (os.environ.get(name) or "").strip() or default


ENV = _get("BIZDNA_ENV", "development")
IS_PRODUCTION = ENV == "production"

# 브라우저에서 API를 직접 호출할 수 있는 웹 주소. 웹은 보통 Next.js rewrites로 호출하므로 개발 주소만 둔다.
CORS_ORIGINS = [x.strip() for x in _get("BIZDNA_CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",") if x.strip()]

# 운영 환경에서는 /docs, /openapi.json을 끈다.
API_DOCS_ENABLED = _get("BIZDNA_API_DOCS", "false" if IS_PRODUCTION else "true").lower() == "true"

# ---- Supabase (FR-01 로그인, FR-12 저장). Vercel의 Supabase 연동이 자동 등록한다. ----
# 비어 있으면 로그인·저장 API가 503을 돌려주고 나머지 기능(게스트 진단)은 그대로 동작한다.
SUPABASE_URL = _get("SUPABASE_URL", _get("NEXT_PUBLIC_SUPABASE_URL", "")).rstrip("/")
# 구형(HS256) 프로젝트의 JWT 비밀값. 새 프로젝트는 비대칭 키(JWKS)로 검증하므로 비워 둬도 된다.
SUPABASE_JWT_SECRET = _get("SUPABASE_JWT_SECRET", "")
# 풀링 연결(트랜잭션 풀러). 마이그레이션은 POSTGRES_URL_NON_POOLING을 쓴다.
POSTGRES_URL = _get("POSTGRES_URL", "")
POSTGRES_URL_NON_POOLING = _get("POSTGRES_URL_NON_POOLING", "")
# 관리자 키(가입 처리용). 절대 웹 쪽 변수에 두지 않는다. 구형 연동 이름(SERVICE_ROLE_KEY)도 받는다.
SUPABASE_SECRET_KEY = _get("SUPABASE_SECRET_KEY", _get("SUPABASE_SERVICE_ROLE_KEY", ""))
