"""결측·경계값·위험 임계값·적자 규칙 단위 테스트 (CLAUDE.md 10장)."""
import copy

import pytest
from fixtures import case

import sosang.engine as eng
from sosang import DiagnosticError, diagnose, grade_for, load_model

MODEL = load_model()


def base():
    return case("sample_cafe")


def area(r, code):
    return next(a for a in r["competence"]["areas"] if a["code"] == code)


def strategy(r, code):
    return next((s for s in r["strategies"]["items"] if s["area"] == code), None)


# ---- DNA 경계값 (50 이상 A 문자, 40 초과 60 미만 경계)

@pytest.mark.parametrize("vals,score,letter,boundary,lean", [
    ([3, 3, 3, 3], 50.0, "G", True, "경계"),
    ([3, 3, 3, 2], 43.75, "S", True, "경계"),
    ([3, 3, 2, 2], 37.5, "S", False, "안정생계형"),
    ([4, 3, 3, 3], 56.25, "G", True, "경계"),
    ([4, 4, 3, 3], 62.5, "G", False, "성장확대형"),
])
def test_dna_boundaries(vals, score, letter, boundary, lean):
    p = base()
    for i, v in enumerate(vals):
        p["answers"]["dna"][f"D{i + 1:02d}"] = v
    goal = diagnose(p)["dna"]["axes"][0]
    assert (goal["score"], goal["letter"], goal["boundary"], goal["lean"]) == (score, letter, boundary, lean)


def test_dna_missing_axis_gives_no_type():
    p = base()
    for i in range(13, 17):
        p["answers"]["dna"][f"D{i:02d}"] = None
    r = diagnose(p)
    assert r["dna"]["code"] is None and r["dna"]["axes"][3]["answered"] == 0
    assert len(r["dna"]["missing"]) == 4


def test_dna_partial_axis_uses_answered_only():
    p = base()
    p["answers"]["dna"]["D01"] = None  # 나머지 4,3,4 → 8/12
    assert diagnose(p)["dna"]["axes"][0]["score"] == 66.67


# ---- 등급 경계 (하한 포함)

@pytest.mark.parametrize("total,grade", [(85, "A"), (84.99, "B"), (70, "B"), (55, "C"), (54.99, "D"),
                                         (40, "D"), (39.99, "E"), (0, "E")])
def test_grade_boundaries(total, grade):
    assert grade_for(total, MODEL)["grade"] == grade


# ---- 역량 결측

def test_missing_item_is_not_zero():
    p = base()
    p["answers"]["competence"]["A04"] = None  # A: 3,3,4 → 7/12
    r = diagnose(p)
    assert area(r, "A")["score"] == 58.33
    assert r["competence"]["missing_ratio"] == round(1 / 32, 4)


def test_missing_area_is_excluded_and_weights_renormalized():
    p = base()
    for i in range(1, 5):
        p["answers"]["competence"][f"G{i:02d}"] = None
    r = diagnose(p)
    assert r["competence"]["excluded_areas"] == ["G"]
    w = MODEL["competence"]["weights"]["food"]
    s = {a["code"]: a["score"] for a in r["competence"]["areas"] if a["score"] is not None}
    assert r["competence"]["total"] == round(sum(s[k] * w[k] for k in s) / (100 - w["G"]), 2)
    assert strategy(r, "G") is None


def test_no_competence_answers_gives_no_total_or_strategy():
    p = base()
    p["answers"]["competence"] = {}
    r = diagnose(p)
    assert r["competence"]["total"] is None and r["strategies"] is None
    assert "WEAK_FINANCE" not in [x["code"] for x in r["risks"]]


def test_partial_special_area_blends_answered_items():
    p = base()
    p["answers"]["special"] = {"FOOD-B01": 5, "FOOD-B02": 5}
    r = diagnose(p)
    assert area(r, "B")["special_score"] == 100.0
    assert area(r, "B")["score"] == round(.65 * 75 + .35 * 100, 2)
    assert r["competence"]["special_areas"] == ["B"]


def test_other_sector_ignores_special_answers_and_uses_default_weights():
    p = base()
    p["store"]["sector_group"] = "other"
    p["answers"]["special"] = {"FOOD-B01": 5}
    r = diagnose(p)
    assert r["competence"]["special_areas"] == []
    assert r["competence"]["weights"] == MODEL["competence"]["weights"]["default"]


# ---- 업종 대응

@pytest.mark.parametrize("store,group", [
    ({"major": "FOOD"}, "food"), ({"major": "WHOLESALE"}, "retail"), ({"major": "LIFE"}, "life"),
    ({"major": "MAKE"}, "other"), ({"biz_model": "M11"}, "life"), ({}, "other"),
])
def test_sector_group_resolution(store, group):
    p = base()
    p["store"] = store
    assert diagnose(p)["store"]["sector_group"] == group


# ---- 위험 임계값

def risks_for(sales, rent=0, other=0):
    p = base()
    p["finance"] = {"monthly_sales": sales, "rent": rent, "other_cost": other}
    return [x["code"] for x in diagnose(p)["risks"]]


def test_rent_burden_threshold_is_exclusive():
    assert "RENT_BURDEN" not in risks_for(1000, rent=200)
    assert "RENT_BURDEN" in risks_for(1000, rent=201)


def test_low_buffer_threshold_is_exclusive():
    assert "LOW_BUFFER" not in risks_for(1000, other=950)
    assert "LOW_BUFFER" in risks_for(1000, other=951)


def test_zero_residual_is_not_deficit():
    assert "NEGATIVE_CASH" not in risks_for(1000, other=1000)
    assert "NEGATIVE_CASH" in risks_for(1000, other=1001)


def test_no_sales():
    risks = risks_for(0, other=100)
    assert risks[:2] == ["NO_SALES", "NEGATIVE_CASH"] and "RENT_BURDEN" not in risks
    p = base()
    p["finance"] = {"monthly_sales": 0}
    assert diagnose(p)["finance"]["rent_ratio_pct"] is None


def test_weak_finance_threshold():
    p = base()
    p["answers"]["competence"].update({"E01": 3, "E02": 3, "E03": 2, "E04": 2})  # 37.5
    assert "WEAK_FINANCE" in [x["code"] for x in diagnose(p)["risks"]]
    p["answers"]["competence"].update({"E01": 3, "E02": 3, "E03": 3, "E04": 2})  # 43.75
    assert "WEAK_FINANCE" not in [x["code"] for x in diagnose(p)["risks"]]


def test_itemized_costs_sum():
    p = base()
    p["finance"] = {"monthly_sales": 2200, "material_cost": 900, "labor_cost": 600, "rent": 320, "other_cost": 280}
    r = diagnose(p)
    assert r["finance"]["total_cost"] == 2100 and r["finance"]["operating_residual"] == 100
    assert r["competence"]["total"] == diagnose(base())["competence"]["total"]
    assert r["finance"]["material_ratio_pct"] == 40.91


# ---- 적자 규칙

def test_deficit_puts_finance_first_and_gates_expansion():
    p = base()
    p["finance"] = {"monthly_sales": 1000, "rent": 100, "other_cost": 1200}
    items = diagnose(p)["strategies"]["items"]
    assert items[0]["area"] == "E" and items[0]["urgency"] == 95 and items[0]["fit"] == 100
    assert "DEFICIT_FINANCE_FIRST" in items[0]["rules"]
    for s in items:
        if s["area"] in ("A", "D"):
            assert s["gated"] and s["priority"] <= 35 and "확장성 지출" in s["rationale"]


def test_deficit_floor_can_be_disabled_for_v4_parity(monkeypatch):
    p = base()
    p["finance"] = {"monthly_sales": 1000, "other_cost": 1200}
    model = copy.deepcopy(MODEL)
    model["strategy"]["rules"]["reapply_deficit_floor"] = False
    monkeypatch.setattr(eng, "load_model", lambda name: model)
    assert strategy(eng.diagnose(p), "E")["urgency"] == 75.0  # v4 원본: 100 − 25


def test_goal_bonus():
    p = base()
    p["store"]["goal"] = "efficiency"
    r = diagnose(p)
    assert r["strategies"]["goal_area"] == "F" and r["store"]["goal_name"] == "운영효율"
    f = strategy(r, "F")
    assert f is not None and "GOAL_EFFICIENCY" in f["rules"] and "FOOD_OPERATION" in f["rules"]
    assert f["fit"] == 50 + 8 + 18


# ---- 성장단계 (월매출 2200: 2200/1900 − 1 = 15.79%)

@pytest.mark.parametrize("obs,stage", [
    ({"months_operating": 5, "repeat_rate": 50, "positive_cashflow_months": 12}, "S1"),
    ({"months_operating": 30, "repeat_rate": 9, "positive_cashflow_months": 12}, "S1"),
    ({"months_operating": 11, "repeat_rate": 50, "positive_cashflow_months": 12}, "S2"),
    ({"months_operating": 30, "repeat_rate": 24, "positive_cashflow_months": 12}, "S2"),
    ({"months_operating": 30, "repeat_rate": 50, "positive_cashflow_months": 8, "sales_prev": 1000}, "S3"),
    ({"months_operating": 30, "repeat_rate": 50, "positive_cashflow_months": 12}, "S3"),
    ({"months_operating": 30, "repeat_rate": 50, "positive_cashflow_months": 9, "sales_prev": 1900,
      "channels": 2, "staff": 2}, "S4"),
    ({"months_operating": 30, "repeat_rate": 50, "positive_cashflow_months": 9, "sales_prev": 1900,
      "channels": 1, "staff": 2}, "S3"),
    ({"months_operating": 30, "repeat_rate": 50}, "UNDETERMINED"),
])
def test_stage(obs, stage):
    p = base()
    p["observations"] = obs
    assert diagnose(p)["stage"]["code"] == stage


# ---- 입력 검증

@pytest.mark.parametrize("mutate", [
    lambda p: p["answers"]["competence"].update({"A01": 6}),
    lambda p: p["answers"]["dna"].update({"D01": 0}),
    lambda p: p["answers"]["competence"].update({"A01": True}),
    lambda p: p["finance"].update({"monthly_sales": -1}),
    lambda p: p["finance"].update({"monthly_sales": float("inf")}),
    lambda p: p["finance"].pop("monthly_sales"),
    lambda p: p.update({"observations": {"repeat_rate": 101}}),
    lambda p: p.update({"observations": {"positive_cashflow_months": 13}}),
    lambda p: p["store"].update({"goal": "x"}),
    lambda p: p["store"].update({"sector_group": "x"}),
])
def test_invalid_input(mutate):
    p = base()
    mutate(p)
    with pytest.raises(DiagnosticError):
        diagnose(p)


def test_benchmark_is_labeled_user_supplied():
    p = base()
    p["benchmark"] = {"monthly_sales": 2000}
    b = diagnose(p)["benchmark"]
    assert b["gap_pct"] == 10.0 and "공식 업종 평균으로 검증되지 않음" in b["warning"]


def test_deterministic_and_versioned():
    assert diagnose(base()) == diagnose(base())
    assert all(v.startswith("sosang-") for v in diagnose(base())["versions"].values())
