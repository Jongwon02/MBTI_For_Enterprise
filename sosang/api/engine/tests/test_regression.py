"""CLAUDE.md 4.9 기준 사례. 엔진을 고칠 때 항상 통과해야 한다 (v4 advanced.diagnose_v4 실행값)."""
import pytest
from fixtures import case, load_v4, from_v4

from sosang import diagnose


def scores(r):
    return [a["score"] for a in r["competence"]["areas"]]


def ranking(r):
    return [(s["title"], s["priority"]) for s in r["strategies"]["items"]]


def test_case1_cafe_common_only():
    r = diagnose(case("sample_cafe"))
    assert [a["score"] for a in r["dna"]["axes"]] == [68.75, 81.25, 31.25, 25.0]
    assert r["dna"]["code"] == "GDRO" and r["dna"]["name"] == "점주주도 차별화형"
    assert r["dna"]["boundary_axes"] == []
    assert scores(r) == [50, 75, 75, 25, 25, 50, 25, 50]
    assert r["competence"]["total"] == 48.75
    assert r["finance"]["operating_residual"] == 100
    assert r["finance"]["rent_ratio_pct"] == 14.55
    assert [x["code"] for x in r["risks"]] == ["LOW_BUFFER", "WEAK_FINANCE"]
    assert r["stage"]["code"] == "UNDETERMINED"
    assert r["confidence"]["level"] == "제한적"
    assert ranking(r) == [("수익구조 및 현금흐름 개선", 79.95), ("신규고객 유입 강화", 65.25),
                          ("디지털 경영관리 도입", 63.25), ("점포 운영효율 개선", 56.8),
                          ("경영목표 및 대응계획 수립", 54.0)]


def test_case2_service_common_only():
    r = diagnose(case("sample_service"))
    assert [a["score"] for a in r["dna"]["axes"]] == [31.25, 62.5, 31.25, 31.25]
    assert r["dna"]["code"] == "SDRO" and r["dna"]["boundary_axes"] == []
    assert scores(r) == [75, 75, 25, 25, 75, 50, 25, 50]
    assert r["competence"]["total"] == 52.25
    assert r["finance"]["operating_residual"] == 500
    assert r["finance"]["rent_ratio_pct"] == 7.22
    assert r["risks"] == []
    assert r["stage"]["code"] == "UNDETERMINED" and r["confidence"]["level"] == "제한적"
    assert ranking(r) == [("단골고객 및 재방문 확대", 73.65), ("신규고객 유입 강화", 69.45),
                          ("디지털 경영관리 도입", 63.25), ("점포 운영효율 개선", 59.6),
                          ("경영목표 및 대응계획 수립", 54.0)]


def test_case3_cafe_with_special_and_observations():
    r = diagnose(case("example_cafe_v4"))
    assert r["sales_growth_pct"] == 8.7
    assert scores(r) == [50, 70.62, 70.62, 25, 25, 54.38, 25, 50]
    assert r["competence"]["total"] == 47.92
    assert [x["code"] for x in r["risks"]] == ["LOW_BUFFER", "WEAK_FINANCE"]
    assert r["stage"]["code"] == "S3" and r["confidence"]["level"] == "보통"
    assert ranking(r) == [("수익구조 및 현금흐름 개선", 79.95), ("신규고객 유입 강화", 65.25),
                          ("디지털 경영관리 도입", 63.25), ("점포 운영효율 개선", 54.83),
                          ("경영목표 및 대응계획 수립", 54.0)]


def test_case4_service_with_special_and_observations():
    r = diagnose(case("example_service_v4"))
    assert r["sales_growth_pct"] == 8.7
    assert scores(r) == [75, 70.62, 38.12, 25, 75, 54.38, 25, 50]
    assert r["competence"]["total"] == 54.66
    assert r["risks"] == []
    assert r["stage"]["code"] == "S3" and r["confidence"]["level"] == "보통"
    assert ranking(r) == [("신규고객 유입 강화", 69.45), ("단골고객 및 재방문 확대", 67.75),
                          ("디지털 경영관리 도입", 63.25), ("점포 운영효율 개선", 57.63),
                          ("경영목표 및 대응계획 수립", 54.0)]


@pytest.mark.parametrize("name", ["sample_cafe", "sample_service"])
def test_v4_scenario_stage_s4(name):
    """legacy/mvp_v4/test_v4.py 시나리오."""
    v4 = load_v4(name)
    sector = {"외식업": ["상품·서비스", "고객관리", "점포운영"], "생활서비스업": ["상품·서비스", "고객관리", "점포운영"]}
    v4["sector_answers"] = {a: [5, 4, 4, 3] for a in sector[v4["profile"]["sector"]]}
    v4["observations"] = {"months_operating": 30, "repeat_rate": 50, "positive_cashflow_months": 10,
                          "channels": 2, "staff": 3, "sales_prev": v4["profile"]["monthly_sales"] * .8}
    r = diagnose(from_v4(v4))
    assert r["stage"]["code"] == "S4"
    assert len(r["competence"]["special_areas"]) == 3
    assert r["confidence"]["level"] == "보통"
    assert 0 <= r["competence"]["total"] <= 100
    assert len(r["strategies"]["top"]) == 3
