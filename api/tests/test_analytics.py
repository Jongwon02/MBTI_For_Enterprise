"""경영자 성향 데이터 수집(CLAUDE.md 12.4·12.5·12.11). derive_rows와 방향값 함수는 DB 없이 검사한다."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "api"))
sys.path.insert(0, str(ROOT / "api" / "engine"))
sys.path.insert(0, str(ROOT / "api" / "engine" / "tests"))

from bizdna import diagnose_survey, load_model  # noqa: E402
from bizdna_api.analytics import (  # noqa: E402
    axis_direction, axis_score, derive_rows, direction_boundary, direction_letter, summarize_facts,
)
from fixtures import as_survey, case  # noqa: E402

MODEL = load_model()
SK = "33333333-3333-3333-3333-333333333333"
SECRET_TEXT = "비밀기업명-식별문자열"


def diagnosis(name="case_a", phase="full", survey=None):
    survey = survey or as_survey(case(name))
    result = diagnose_survey(survey, phase)
    return {"id": "44444444-4444-4444-4444-444444444444", "created_by": "55555555-5555-5555-5555-555555555555",
            "company_name": survey["company"].get("name"), "phase": phase,
            "status": "full_completed" if phase == "full" else "basic_completed",
            "survey": survey, "result": result, "model_version": result["model_version"],
            "questions_version": result["questions_version"], "completed_at": datetime.now(timezone.utc)}


# ---- 12.4 방향값 ---------------------------------------------------------------

@pytest.mark.parametrize("s", [0, 40, 50, 60, 100, 79.17, 33.33, 29.17, 41.67, 58.33])
def test_round_trip(s):
    assert axis_score(axis_direction(s)) == s


def test_direction_range_and_null():
    assert axis_direction(100) == 100 and axis_direction(0) == -100 and axis_direction(50) == 0
    assert axis_direction(None) is None and axis_score(None) is None


@pytest.mark.parametrize("score,boundary", [(40, False), (60, False), (40.01, True), (59.99, True), (50, True), (39.99, False)])
def test_boundary_from_direction(score, boundary):
    # 점수 40·60(방향 −20·+20)은 경계가 아니다(4.2: 60 이상 A, 40 이하 B)
    assert direction_boundary(axis_direction(score), MODEL) is boundary


def test_letter_from_direction():
    assert direction_letter(0, "G", "S", MODEL) == "G"
    assert direction_letter(-0.01, "G", "S", MODEL) == "S"


@pytest.mark.parametrize("name", ["case_a", "case_b"])
def test_dna_type_matches_reversed_letters(name):
    fact = derive_rows(diagnosis(name), subject_key=SK, round_no=1).fact
    letters = "".join(direction_letter(fact[f"dna_{c}_dir"], ax["a"], ax["b"], MODEL)
                      for c, ax in zip("ginp", MODEL["dna"]["axes"]))
    assert letters == fact["dna_type"]


# ---- 12.5 화이트리스트 -----------------------------------------------------------

def test_full_diagnosis_rows():
    rows = derive_rows(diagnosis("case_a"), subject_key=SK, round_no=2)
    f = rows.fact
    assert f["dna_type"] == "GICO" and f["stage_code"] == "S3" and f["total_score"] == 61.87 and f["grade"] == "C"
    assert f["dna_g_dir"] == axis_direction(79.17) and f["dna_g_answered"] == 6
    assert f["industry"] == "제조업" and f["founded_year"] == 2023 and f["employees"] == 7
    assert f["customer_type"] == ["기업(B2B)"]
    assert f["stage_product"] == 4 and f["stage_cash"] == 2
    assert f["subject_key"] == SK and f["round_no"] == 2 and f["phase"] == "full"
    assert f["goals"] and all(g in MODEL["goals"] for g in f["goals"])
    assert f["risk_flags"] and all(r in MODEL["risks"] for r in f["risk_flags"])
    assert [d["domain"] for d in rows.domain_scores] == list("ABCDEFGH")
    assert all(d["answered"] == 8 for d in rows.domain_scores)
    assert len(rows.strategy_scores) == 12 and [s["rank"] for s in rows.strategy_scores] == list(range(1, 13))
    assert rows.strategy_scores[0]["strategy"] == "ST07"


def test_basic_diagnosis_has_no_competence_rows():
    rows = derive_rows(diagnosis("case_a", phase="basic"), subject_key=SK, round_no=1)
    assert rows.fact["total_score"] is None and rows.fact["grade"] is None
    assert rows.domain_scores == [] and rows.strategy_scores == []
    assert rows.fact["dna_type"] == "GICO"


def test_missing_axis_and_domain():
    survey = as_survey(case("case_a"))
    for code in ("D13", "D14", "D15", "D16", "D17", "D18"):  # 시장전략 축 전체 결측
        survey["answers"]["dna"].pop(code)
    for code in ("A01", "A02", "A03"):
        survey["answers"]["competence"].pop(code)
    rows = derive_rows(diagnosis(survey=survey), subject_key=SK, round_no=1)
    assert rows.fact["dna_n_dir"] is None and rows.fact["dna_n_answered"] == 0
    assert next(d for d in rows.domain_scores if d["domain"] == "A")["answered"] == 5


def test_identifying_values_never_leak():
    """기업명·자유서술·회원 ID·원본에 섞인 임의 키가 분석 행 어디에도 들어가지 않는다."""
    survey = as_survey(case("case_a"))
    survey["company"] |= {"name": SECRET_TEXT, "industry_detail": SECRET_TEXT, "main_channel": SECRET_TEXT,
                          "goal_3y": SECRET_TEXT, "investment_plan": SECRET_TEXT, "unknown_key": SECRET_TEXT}
    survey["answers"]["plan"] |= {"P05": [SECRET_TEXT, "rnd"], "P07": SECRET_TEXT, "P02": SECRET_TEXT,
                                  "P99": SECRET_TEXT, "note": SECRET_TEXT}
    survey["answers"]["stage"]["comment"] = SECRET_TEXT
    d = diagnosis(survey=survey)
    rows = derive_rows(d, subject_key=SK, round_no=1)
    dumped = json.dumps([rows.fact, rows.domain_scores, rows.strategy_scores], ensure_ascii=False, default=str)
    assert SECRET_TEXT not in dumped
    assert d["created_by"] not in dumped
    assert rows.fact["plan"]["P05"] == ["rnd"] and "P07" not in rows.fact["plan"] and "P99" not in rows.fact["plan"]
    assert "name" not in rows.fact and "company_name" not in rows.fact


def test_invalid_company_values_become_null():
    survey = as_survey(case("case_a"))
    survey["company"] |= {"industry": "기타업", "founded_year": "abc", "sales_recent": float("nan"), "employees": True}
    f = derive_rows(diagnosis(survey=survey), subject_key=SK, round_no=1).fact
    assert f["industry"] is None and f["founded_year"] is None and f["sales_recent"] is None and f["employees"] is None


# ---- 관리자 집계 ----------------------------------------------------------------

def test_summarize_facts():
    facts = []
    for name in ("case_a", "case_b"):
        r = derive_rows(diagnosis(name), subject_key=SK if name == "case_a" else "x", round_no=1)
        facts.append(r.fact | {"domains": {d["domain"]: d["score"] for d in r.domain_scores},
                               "top_strategies": [s["strategy"] for s in r.strategy_scores if s["status"] == "recommended"][:3]})
    s = summarize_facts(facts, [{"event": "started"}, {"event": "full_completed"}])
    assert s["n"] == 2 and s["subjects"] == 2 and s["full"] == 2
    assert {x["key"] for x in s["dna_types"]} == {"GICO", "GINO"}
    assert s["axes"][0]["a"] == "G" and s["axes"][0]["n"] == 2 and s["axes"][0]["a_share"] == 1.0
    assert s["total_score"]["p50"] == round((61.87 + 75.16) / 2, 2)
    assert s["funnel"] == {"started": 1, "basic_completed": 0, "full_completed": 1}
    assert s["labels"]["strategies"]["ST07"]


def test_summarize_empty():
    s = summarize_facts([], [])
    assert s["n"] == 0 and s["axes"][0]["mean"] is None and s["total_score"]["p50"] is None
