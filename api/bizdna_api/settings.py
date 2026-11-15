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
