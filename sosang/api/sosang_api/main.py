"""Biz-DNA 소상공인 API. 실행: uvicorn sosang_api.main:app --reload --port 8001 (sosang/api 폴더에서)

경로는 모두 /api/sosang/* 이다(중소경영 API가 /api/* 를 쓴다, sosang/CLAUDE.md 3.3).
게스트 진단(저장 없음)과 회원 진단 저장(sosang.assessments, 본인 회차만)을 제공한다.
회원은 중소경영과 분리된 소상공인 계정만 받는다(sosang/CLAUDE.md 3.4, auth.py·store.is_member).
"""
from __future__ import annotations

import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "engine"))

from sosang import DiagnosticError, diagnose, load_industries, load_model, load_questions  # noqa: E402

from . import settings  # noqa: E402  (.env를 report보다 먼저 읽는다)
from .auth import User, current_user  # noqa: E402
from .report import build_report  # noqa: E402
from .signup import SignupRequest, signup  # noqa: E402
from .store import AssessmentStore, get_store, summarize  # noqa: E402

PREFIX = "/api/sosang"

docs = (
    {"docs_url": f"{PREFIX}/docs", "redoc_url": None, "openapi_url": f"{PREFIX}/openapi.json"}
    if settings.API_DOCS_ENABLED else {"docs_url": None, "redoc_url": None, "openapi_url": None}
)
app = FastAPI(title="Biz-DNA 소상공인 API", version="0.1.0", **docs)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
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


# ---- 회원가입 (아이디 + 비밀번호, 이메일 인증 없음) -------------------------------------------
@app.post(f"{PREFIX}/auth/signup", status_code=201)
def create_account(req: SignupRequest) -> dict[str, Any]:
    return signup(req)


# ---- 회원 진단 저장 (sosang/CLAUDE.md 11장) ------------------------------------------------
# 모든 조회·수정은 로그인한 소상공인 회원 본인의 회차로 제한한다(store가 created_by로 거른다).
# 게스트는 이 API를 쓰지 않고 브라우저(localStorage)에만 저장한다.

class Progress(BaseModel):
    step: int = 0
    maxStep: int = 0
    percent: int = 0  # 필수 문항 응답률(마이페이지 표시용)


class AssessmentSave(BaseModel):
    survey: dict[str, Any]
    progress: Progress = Progress()
    # true면 최종저장: 엔진을 실행해 결과와 모형·문항·업종분류 버전을 함께 저장한다.
    complete: bool = False


def member(user: User = Depends(current_user), store: AssessmentStore = Depends(get_store)) -> User:
    """소상공인 회원(sosang.profiles에 행이 있는 계정)만 통과시킨다."""
    if not store.is_member(user.id):
        raise HTTPException(status_code=403, detail="소상공인 진단 회원 정보가 없습니다. 회원가입 후 이용해 주세요.")
    return user


def _check_id(assessment_id: str) -> str:
    try:
        return str(uuid.UUID(assessment_id))
    except ValueError as e:
        raise HTTPException(status_code=404, detail="진단을 찾을 수 없습니다.") from e


def _fields(req: AssessmentSave) -> dict[str, Any]:
    store_info = req.survey.get("store") or {}
    data: dict[str, Any] = {
        "survey": req.survey,
        "progress": req.progress.model_dump(),
        "store_name": (str(store_info.get("name") or "").strip()[:80] or None),
    }
    if req.complete:
        result = _run(req.survey)
        v = result.get("versions") or {}
        data |= {"result": result, "status": "completed", "model_version": v.get("model"),
                 "questions_version": v.get("questions"), "industries_version": v.get("industries"),
                 "completed_at": datetime.now(timezone.utc)}
    return data


def _not_found() -> HTTPException:
    return HTTPException(status_code=404, detail="진단을 찾을 수 없습니다.")


@app.get(f"{PREFIX}/me")
def me(user: User = Depends(member)) -> dict[str, Any]:
    return {"id": user.id}


@app.get(f"{PREFIX}/assessments")
def list_assessments(user: User = Depends(member), store: AssessmentStore = Depends(get_store)) -> list[dict[str, Any]]:
    return [summarize(r) for r in store.list(user.id)]


@app.post(f"{PREFIX}/assessments", status_code=201)
def create_assessment(req: AssessmentSave, user: User = Depends(member),
                      store: AssessmentStore = Depends(get_store)) -> dict[str, Any]:
    return store.create(user.id, _fields(req))


@app.get(f"{PREFIX}/assessments/{{assessment_id}}")
def get_assessment(assessment_id: str, user: User = Depends(member),
                   store: AssessmentStore = Depends(get_store)) -> dict[str, Any]:
    row = store.get(user.id, _check_id(assessment_id))
    if not row:
        raise _not_found()
    return row


@app.put(f"{PREFIX}/assessments/{{assessment_id}}")
def update_assessment(assessment_id: str, req: AssessmentSave, user: User = Depends(member),
                      store: AssessmentStore = Depends(get_store)) -> dict[str, Any]:
    aid = _check_id(assessment_id)
    if not store.get(user.id, aid):
        raise _not_found()
    # 중간저장은 상태·결과를 건드리지 않는다. 완료한 회차를 고쳐 다시 최종저장하면 결과가 바뀐다.
    row = store.update(user.id, aid, _fields(req))
    if not row:
        raise _not_found()
    return row


@app.delete(f"{PREFIX}/assessments/{{assessment_id}}", status_code=204)
def delete_assessment(assessment_id: str, user: User = Depends(member),
                      store: AssessmentStore = Depends(get_store)) -> Response:
    if not store.delete(user.id, _check_id(assessment_id)):
        raise _not_found()
    return Response(status_code=204)
