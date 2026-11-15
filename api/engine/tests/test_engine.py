import pytest

from bizdna import DiagnosticError, completeness, diagnose, diagnose_survey, grade_for, load_model, to_engine_payload
from fixtures import as_survey, case


def test_missing_answer_is_recorded_not_zero():
    p = case("case_a")
    del p["answers"]["dna"]["D01"]
    del p["answers"]["competence"]["A01"]
    r = diagnose(p)
    assert r["dna"]["missing"] == ["D01"]
    assert r["dna"]["axes"]["성장지향"]["answered"] == 5
    assert r["competence"]["missing"] == ["A01"]
    # 응답한 7문항만으로 환산해야 한다(결측을 1점으로 채우지 않는다).
    remaining = [v for k, v in p["answers"]["competence"].items() if k.startswith("A")]
    assert r["competence"]["domains"]["A"] == round(sum(x - 1 for x in remaining) / (4 * len(remaining)) * 100, 2)


def test_whole_axis_missing_marks_unknown_letter():
    p = case("case_b")
    for n in range(19, 25):
        del p["answers"]["dna"][f"D{n:02d}"]
    r = diagnose(p)
    assert r["dna"]["type"] == "GIN?"
    assert r["dna"]["complete"] is False
    assert r["dna"]["name"] is None


def test_bad_range_raises():
    p = case("case_b")
    p["answers"]["competence"]["A01"] = 7
    with pytest.raises(DiagnosticError):
        diagnose(p)


def test_market_gate():
    p = case("case_b")
    p["answers"]["stage"]["customer"] = 2
    r = diagnose(p)
    assert r["stage"]["level"] <= 2
    assert r["stage"]["gate_adjusted"] is True
    assert r["stage"]["gates_applied"]


def test_cash_rule_defers_scaleup():
    p = case("case_b")
    p["flags"]["cash_crisis"] = True
    st11 = next(s for s in diagnose(p)["strategies"] if s["code"] == "ST11")
    assert st11["status"] == "deferred"
    assert "R-CASH" in st11["applied_rules"]


@pytest.mark.parametrize("score,boundary", [(37.5, False), (41.67, True), (58.33, True), (62.5, False)])
def test_dna_boundary(score, boundary):
    p = case("case_a")
    total = round(score / 100 * 24)  # 6문항 합계 - 6
    values = [1] * 6
    for j in range(total):
        values[j % 6] += 1
    for j, v in enumerate(values):
        p["answers"]["dna"][f"D{j + 1:02d}"] = v
    axis = diagnose(p)["dna"]["axes"]["성장지향"]
    assert axis["score"] == score
    assert axis["boundary"] is boundary


@pytest.mark.parametrize("total,grade", [(85, "A"), (84.99, "B"), (70, "B"), (69.99, "C"), (55, "C"), (54.99, "D"), (40, "D"), (39.99, "E"), (0, "E")])
def test_grade_boundaries(total, grade):
    assert grade_for(total, load_model())["grade"] == grade


def test_basic_mode_without_competence():
    p = case("case_a")
    p["answers"]["competence"] = {}
    r = diagnose(p)
    assert r["mode"] == "basic"
    assert r["competence"] is None and r["strategies"] is None
    assert r["dna"]["type"] == "GICO" and r["stage"]["code"] == "S3"


def test_survey_mapping_and_result():
    survey = as_survey(case("case_a"))
    payload = to_engine_payload(survey)
    assert payload["goals"] == ["profit", "market", "funding"]
    assert payload["flags"] == {"negative_unit_margin": True, "founder_bottleneck": True, "funding_gap": True}
    r = diagnose_survey(survey, "full")
    assert r["competence"]["total"] == 61.87
    assert r["top_recommended"][0]["code"] == "ST07"
    assert r["questions_version"] == "questions-1.0"


def test_survey_non_risk_obstacle_is_ignored_by_engine():
    survey = as_survey(case("case_b"))
    survey["answers"]["plan"]["P09"] = ["talent", "founder_bottleneck"]
    assert to_engine_payload(survey)["flags"] == {"founder_bottleneck": True}


def test_survey_basic_requires_stage_and_goal():
    survey = as_survey(case("case_a"))
    del survey["answers"]["stage"]["cash"]
    survey["answers"]["plan"]["P01"] = []
    status = completeness(survey)
    assert status["basic_ready"] is False
    with pytest.raises(DiagnosticError, match="cash"):
        diagnose_survey(survey, "basic")


def test_survey_rejects_too_many_goals():
    survey = as_survey(case("case_a"))
    survey["answers"]["plan"]["P01"] = ["profit", "market", "funding", "scale"]
    with pytest.raises(DiagnosticError, match="최대 3개"):
        to_engine_payload(survey)


def test_survey_basic_phase_ignores_competence():
    r = diagnose_survey(as_survey(case("case_b")), "basic")
    assert r["mode"] == "basic"
    assert r["dna"]["type"] == "GINO"
