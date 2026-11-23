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
