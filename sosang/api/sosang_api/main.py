"""Biz-DNA 소상공인 API. 실행: uvicorn sosang_api.main:app --reload --port 8001 (sosang/api 폴더에서)

경로는 모두 /api/sosang/* 이다(중소경영 API가 /api/* 를 쓴다, sosang/CLAUDE.md 3.3).
지금은 게스트 진단(저장 없음)만 제공한다. 회원·저장 API는 계정 분리(3.4)를 마친 뒤 붙인다.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any
from urllib.parse import quote

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "engine"))

from sosang import DiagnosticError, diagnose, load_industries, load_model, load_questions  # noqa: E402

from . import settings  # noqa: E402  (.env를 report보다 먼저 읽는다)
from .report import build_report  # noqa: E402

PREFIX = "/api/sosang"

docs = (
    {"docs_url": f"{PREFIX}/docs", "redoc_url": None, "openapi_url": f"{PREFIX}/openapi.json"}
    if settings.API_DOCS_ENABLED else {"docs_url": None, "redoc_url": None, "openapi_url": None}
)
app = FastAPI(title="Biz-DNA 소상공인 API", version="0.1.0", **docs)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class SurveyRequest(BaseModel):
    # 웹의 응답 상태는 엔진 입력(store·finance·answers·observations·benchmark)과 같은 모양이다.
    survey: dict[str, Any]


@app.get(f"{PREFIX}/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get(f"{PREFIX}/questions")
def questions() -> dict[str, Any]:
    """화면에 필요한 문항·업종분류와 모형의 표시용 값(점수 계산 값은 보내지 않는다)."""
    model = load_model()
    return {
        "questions": load_questions(),
        "industries": load_industries(),
        "model": {
            "version": model["version"],
            "areas": model["competence"]["areas"],
            "dna_axes": [{k: a[k] for k in ("key", "name", "a", "b", "a_name", "b_name", "items")} for a in model["dna"]["axes"]],
            "types": model["types"],
            "goals": model["goals"],
            "sector_groups": model["sector_groups"],
            "stage_labels": model["stage"]["labels"],
            "notices": model["notices"],
        },
    }


def _run(survey: dict[str, Any]) -> dict[str, Any]:
    try:
        return diagnose(survey)
    except DiagnosticError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e


@app.post(f"{PREFIX}/diagnose")
def run_diagnosis(req: SurveyRequest) -> dict[str, Any]:
    return _run(req.survey)


@app.post(f"{PREFIX}/report")
def report(req: SurveyRequest) -> Response:
    result = _run(req.survey)
    if result["strategies"] is None:
        raise HTTPException(status_code=422, detail="경영역량 문항에 답해야 보고서를 만들 수 있습니다.")
    pdf = build_report(result)
    filename = f"소상공인진단_{result['store']['name']}_기본형.pdf"
    return Response(pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"})
