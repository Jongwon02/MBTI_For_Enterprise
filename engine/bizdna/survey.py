"""웹 설문 응답을 엔진 입력으로 바꾸고, 응답 완결성을 점검한다 (FR-03, FR-04).

설문 응답 구조:
    {company: {...}, answers: {dna: {D01: 1~5}, stage: {product: 1~5}, competence: {A01: 1~5}, plan: {P01: [...], P02: 3.5}}}

P01 경영목표는 엔진의 goals로, P09 성장장애는 위험 플래그로 바뀐다(초안 매핑, questions_v1.json의 maps_to).
"""
from __future__ import annotations

from typing import Any

from .config import load_model, load_questions
from .engine import DiagnosticError, diagnose

PHASES = ("basic", "full")


def _plan_item(questions: dict[str, Any], code: str) -> dict[str, Any]:
    return next(i for i in questions["plan"]["items"] if i["code"] == code)


def _choices(value: Any, item: dict[str, Any]) -> list[str]:
    if value in (None, ""):
        return []
    if not isinstance(value, list) or any(not isinstance(v, str) for v in value):
        raise DiagnosticError(f"{item['code']}: 선택값 목록 필요")
    allowed = {o["value"] for o in item["options"]}
    bad = [v for v in value if v not in allowed]
    if bad:
        raise DiagnosticError(f"{item['code']}: 허용되지 않은 선택값 {bad}")
    if len(value) > item.get("max", len(allowed)):
        raise DiagnosticError(f"{item['code']}: 최대 {item['max']}개까지 선택")
    return list(dict.fromkeys(value))


def to_engine_payload(survey: dict[str, Any], questions: dict[str, Any] | None = None) -> dict[str, Any]:
    questions = questions or load_questions()
    if not isinstance(survey, dict):
        raise DiagnosticError("설문 응답은 객체여야 함")
    answers = survey.get("answers", {}) or {}
    plan = answers.get("plan", {}) or {}
    model = load_model()
    goals = _choices(plan.get("P01"), _plan_item(questions, "P01"))
    obstacles = _choices(plan.get("P09"), _plan_item(questions, "P09"))
    flags = {k: True for k in obstacles if k in model["risks"]}
    return {
        "company": survey.get("company", {}) or {},
        "answers": {
            "dna": answers.get("dna", {}) or {},
            "stage": answers.get("stage", {}) or {},
            "competence": answers.get("competence", {}) or {},
        },
        "goals": goals,
        "flags": flags,
    }


def completeness(survey: dict[str, Any], questions: dict[str, Any] | None = None) -> dict[str, Any]:
    """단계별 미응답 문항 목록. 미응답은 0점으로 채우지 않고 결측으로 남긴다."""
    questions = questions or load_questions()
    company = survey.get("company", {}) or {}
    answers = survey.get("answers", {}) or {}
    dna = answers.get("dna", {}) or {}
    stage = answers.get("stage", {}) or {}
    comp = answers.get("competence", {}) or {}
    plan = answers.get("plan", {}) or {}

    def empty(v: Any) -> bool:
        return v is None or v == "" or v == []

    company_missing = [f["key"] for f in questions["company_fields"] if f.get("required") and empty(company.get(f["key"]))]
    dna_missing = [i["code"] for i in questions["dna"]["items"] if empty(dna.get(i["code"]))]
    stage_missing = [i["key"] for i in questions["stage"]["items"] if empty(stage.get(i["key"]))]
    comp_missing = [i["code"] for d in questions["competence"]["domains"] for i in d["items"] if empty(comp.get(i["code"]))]
    plan_required = [i["code"] for i in questions["plan"]["items"] if i.get("required") and empty(plan.get(i["code"]))]
    return {
        "company": company_missing,
        "dna": dna_missing,
        "stage": stage_missing,
        "competence": comp_missing,
        "plan_required": plan_required,
        # 기본진단 결과를 내려면 기업정보·성장단계·경영목표가 있어야 한다. DNA 결측은 허용하되 기록한다.
        "basic_ready": not company_missing and not stage_missing and not plan_required and len(dna_missing) < len(questions["dna"]["items"]),
        "full_ready": len(comp_missing) < sum(len(d["items"]) for d in questions["competence"]["domains"]),
    }


def diagnose_survey(survey: dict[str, Any], phase: str = "full") -> dict[str, Any]:
    if phase not in PHASES:
        raise DiagnosticError("phase: basic 또는 full")
    questions = load_questions()
    status = completeness(survey, questions)
    if not status["basic_ready"]:
        missing = status["company"] + status["stage"] + status["plan_required"]
        raise DiagnosticError("기본진단 필수 응답 누락: " + ", ".join(missing) if missing else "DNA 문항에 하나 이상 응답 필요")
    payload = to_engine_payload(survey, questions)
    if phase == "basic":
        payload["answers"]["competence"] = {}
    result = diagnose(payload)
    result["questions_version"] = questions["version"]
    result["completeness"] = status
    result["plan"] = (survey.get("answers", {}) or {}).get("plan", {}) or {}
    return result
