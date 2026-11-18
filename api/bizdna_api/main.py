"""Biz-DNA API. 실행: uvicorn bizdna_api.main:app --reload --port 8000 (api/ 폴더에서)"""
from __future__ import annotations

import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal
from urllib.parse import quote

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "engine"))

from bizdna import DiagnosticError, completeness, diagnose_survey, load_questions  # noqa: E402

from . import settings  # noqa: E402  (.env를 report보다 먼저 읽는다)
from .auth import User, current_user  # noqa: E402
from .report import build_report  # noqa: E402
from .signup import SignupRequest, signup  # noqa: E402
from .store import DiagnosisStore, get_store, summarize  # noqa: E402

docs = {} if settings.API_DOCS_ENABLED else {"docs_url": None, "redoc_url": None, "openapi_url": None}
app = FastAPI(title="Biz-DNA API", version="0.1.0", **docs)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
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


# ---- 회원 진단 저장 (FR-01, FR-12) ------------------------------------------
# 모든 조회·수정은 로그인한 사용자 본인의 회차로 제한한다(store가 created_by로 거른다).
# 게스트는 이 API를 쓰지 않고 브라우저(localStorage)에만 저장한다.

STATUS_RANK = {"draft": 0, "basic_completed": 1, "full_completed": 2}


class Progress(BaseModel):
    step: int = 0
    maxStep: int = 0
    basicDone: bool = False
    phase: Literal["basic", "full"] = "basic"
    percent: int = 0  # 전체 문항 응답률(마이페이지 표시용)


class DiagnosisSave(BaseModel):
    survey: dict[str, Any]
    progress: Progress = Progress()
    # 값이 있으면 최종저장: 엔진을 실행해 결과와 문항·모형 버전을 함께 저장한다.
    complete: Literal["basic", "full"] | None = None


def _check_id(diagnosis_id: str) -> str:
    try:
        return str(uuid.UUID(diagnosis_id))
    except ValueError as e:
        raise HTTPException(status_code=404, detail="진단을 찾을 수 없습니다.") from e


def _fields(req: DiagnosisSave, current_status: str = "draft") -> dict[str, Any]:
    company = req.survey.get("company") or {}
    data: dict[str, Any] = {
        "survey": req.survey,
        "progress": req.progress.model_dump(),
        "company_name": (str(company.get("name") or "").strip() or None),
    }
    if req.complete:
        try:
            result = diagnose_survey(req.survey, req.complete)
        except DiagnosticError as e:
            raise HTTPException(status_code=422, detail=str(e)) from e
        status = "full_completed" if req.complete == "full" else "basic_completed"
        if STATUS_RANK[current_status] > STATUS_RANK[status]:
            status = current_status
        data |= {
            "result": result, "phase": req.complete, "status": status,
            "model_version": result.get("model_version"), "questions_version": result.get("questions_version"),
            "completed_at": datetime.now(timezone.utc),
        }
    return data


@app.get("/api/me")
def me(user: User = Depends(current_user)) -> dict[str, Any]:
    return {"id": user.id, "email": user.email}


@app.get("/api/diagnoses")
def list_diagnoses(user: User = Depends(current_user), store: DiagnosisStore = Depends(get_store)) -> list[dict[str, Any]]:
    return [summarize(r) for r in store.list(user.id)]


@app.post("/api/diagnoses", status_code=201)
def create_diagnosis(req: DiagnosisSave, user: User = Depends(current_user),
                     store: DiagnosisStore = Depends(get_store)) -> dict[str, Any]:
    return store.create(user.id, _fields(req))


@app.get("/api/diagnoses/{diagnosis_id}")
def get_diagnosis(diagnosis_id: str, user: User = Depends(current_user),
                  store: DiagnosisStore = Depends(get_store)) -> dict[str, Any]:
    row = store.get(user.id, _check_id(diagnosis_id))
    if not row:
        raise HTTPException(status_code=404, detail="진단을 찾을 수 없습니다.")
    return row


@app.put("/api/diagnoses/{diagnosis_id}")
def update_diagnosis(diagnosis_id: str, req: DiagnosisSave, user: User = Depends(current_user),
                     store: DiagnosisStore = Depends(get_store)) -> dict[str, Any]:
    did = _check_id(diagnosis_id)
    current = store.get(user.id, did)
    if not current:
        raise HTTPException(status_code=404, detail="진단을 찾을 수 없습니다.")
    # 중간저장은 상태·결과를 건드리지 않는다. 기본진단 완료 후 정밀진단을 이어 할 때 이전 결과는 다음 최종저장까지 유지된다.
    row = store.update(user.id, did, _fields(req, current["status"]))
    if not row:
        raise HTTPException(status_code=404, detail="진단을 찾을 수 없습니다.")
    return row


@app.delete("/api/diagnoses/{diagnosis_id}", status_code=204)
def delete_diagnosis(diagnosis_id: str, user: User = Depends(current_user),
                     store: DiagnosisStore = Depends(get_store)) -> Response:
    if not store.delete(user.id, _check_id(diagnosis_id)):
        raise HTTPException(status_code=404, detail="진단을 찾을 수 없습니다.")
    return Response(status_code=204)


# ---- 회원가입 (FR-01, 아이디 + 비밀번호, 이메일 인증 없음) -----------------------------------------
@app.post("/api/auth/signup", status_code=201)
def create_account(req: SignupRequest) -> dict[str, Any]:
    return signup(req)
