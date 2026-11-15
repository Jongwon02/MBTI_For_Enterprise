"""Biz-DNA API. 실행: uvicorn bizdna_api.main:app --reload --port 8000 (api/ 폴더에서)"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Literal
from urllib.parse import quote

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "engine"))

from bizdna import DiagnosticError, completeness, diagnose_survey, load_questions  # noqa: E402

from . import settings  # noqa: E402  (.env를 report보다 먼저 읽는다)
from .report import build_report  # noqa: E402

docs = {} if settings.API_DOCS_ENABLED else {"docs_url": None, "redoc_url": None, "openapi_url": None}
app = FastAPI(title="Biz-DNA API", version="0.1.0", **docs)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class SurveyRequest(BaseModel):
    survey: dict[str, Any]
    phase: Literal["basic", "full"] = "full"


class ReportRequest(BaseModel):
    survey: dict[str, Any]
    mode: Literal["basic", "advanced"] = "basic"


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/questions")
def questions() -> dict[str, Any]:
    return load_questions()


@app.post("/api/completeness")
def check(req: SurveyRequest) -> dict[str, Any]:
    return completeness(req.survey)


@app.post("/api/diagnose")
def run_diagnosis(req: SurveyRequest) -> dict[str, Any]:
    try:
        return diagnose_survey(req.survey, req.phase)
    except DiagnosticError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e


@app.post("/api/report")
def report(req: ReportRequest) -> Response:
    try:
        result = diagnose_survey(req.survey, "full")
        pdf = build_report(result, req.mode)
    except (DiagnosticError, ValueError) as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    name = (result.get("company") or {}).get("name") or "기업"
    filename = f"BizDNA_{name}_{'기본형' if req.mode == 'basic' else '정밀형'}.pdf"
    return Response(pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"})
