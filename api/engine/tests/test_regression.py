"""PRD 8.7 회귀 테스트. 엔진을 고칠 때마다 이 결과가 유지돼야 한다."""
import importlib.util
from pathlib import Path

import pytest

from bizdna import diagnose
from fixtures import case

LEGACY = Path(__file__).resolve().parents[3] / "legacy" / "bizdna" / "engine.py"


def test_case_a_greenfoodlab():
    r = diagnose(case("case_a"))
    assert r["dna"]["type"] == "GICO"
    assert r["dna"]["name"] == "기술중심 성장형"
    assert r["stage"]["code"] == "S3"
    assert r["competence"]["total"] == 61.87
    assert r["competence"]["grade"]["grade"] == "C"
    top = [(s["code"], s["score"]) for s in r["top_recommended"][:3]]
    assert top == [("ST07", 81.72), ("ST06", 71.34), ("ST08", 61.69)]
    deferred = {s["code"]: s["applied_rules"] for s in r["strategies"] if s["status"] == "deferred"}
    assert deferred == {"ST11": ["R-MARGIN-DEFER"], "ST03": ["R-MARGIN-DEFER"]}


def test_case_b_nextsolution():
    r = diagnose(case("case_b"))
    assert r["dna"]["type"] == "GINO"
    assert r["stage"]["code"] == "S4"
    assert r["competence"]["total"] == 75.16
    assert r["competence"]["grade"]["grade"] == "B"
    top = [(s["code"], s["score"]) for s in r["top_recommended"][:3]]
    assert top == [("ST08", 71.09), ("ST09", 65.75), ("ST03", 65.17)]


@pytest.mark.skipif(not LEGACY.exists(), reason="legacy 원본 없음")
@pytest.mark.parametrize("name", ["case_a", "case_b"])
@pytest.mark.parametrize("extra_flags", [{}, {"cash_crisis": True}, {"market_unvalidated": True, "capacity_shortage": True}])
def test_matches_legacy_engine(name, extra_flags):
    spec = importlib.util.spec_from_file_location("legacy_engine", LEGACY)
    legacy = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(legacy)
    payload = case(name)
    payload["flags"].update(extra_flags)
    old, new = legacy.diagnose(payload), diagnose(payload)
    assert new["dna"]["type"] == old["dna"]["type"]
    assert new["competence"]["domains"] == old["competence"]["domains"]
    assert new["competence"]["total"] == old["competence"]["total"]
    assert new["stage"]["code"] == old["stage"]["code"]
    assert new["risks"] == old["risks"]
    keys = ("code", "score", "status", "factors", "reasons")
    assert [{k: s[k] for k in keys} for s in new["strategies"]] == [{k: s[k] for k in keys} for s in old["strategies"]]
