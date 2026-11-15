import sys
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "api"))
sys.path.insert(0, str(ROOT / "api" / "engine" / "tests"))

from bizdna_api.main import app  # noqa: E402
from fixtures import as_survey, case  # noqa: E402

client = TestClient(app)


def test_questions_has_100_core_items():
    q = client.get("/api/questions").json()
    dna = len(q["dna"]["items"])
    comp = sum(len(d["items"]) for d in q["competence"]["domains"])
    plan = len(q["plan"]["items"])
    assert (dna, comp, plan) == (24, 64, 12)
    assert len(q["stage"]["items"]) == 6


def test_basic_diagnosis():
    r = client.post("/api/diagnose", json={"survey": as_survey(case("case_b")), "phase": "basic"})
    assert r.status_code == 200
    body = r.json()
    assert body["mode"] == "basic" and body["dna"]["type"] == "GINO" and body["stage"]["code"] == "S4"


def test_full_diagnosis_matches_regression():
    body = client.post("/api/diagnose", json={"survey": as_survey(case("case_a"))}).json()
    assert body["competence"]["total"] == 61.87
    assert [s["code"] for s in body["top_recommended"][:3]] == ["ST07", "ST06", "ST08"]


def test_missing_stage_returns_422():
    survey = as_survey(case("case_a"))
    survey["answers"]["stage"] = {}
    r = client.post("/api/diagnose", json={"survey": survey, "phase": "basic"})
    assert r.status_code == 422
    assert "product" in r.json()["detail"]


def test_report_pdf_basic_and_advanced():
    for mode in ("basic", "advanced"):
        r = client.post("/api/report", json={"survey": as_survey(case("case_a")), "mode": mode})
        assert r.status_code == 200, r.text
        assert r.headers["content-type"] == "application/pdf"
        assert r.content[:4] == b"%PDF"


def test_report_requires_competence():
    survey = as_survey(case("case_a"))
    survey["answers"]["competence"] = {}
    r = client.post("/api/report", json={"survey": survey, "mode": "basic"})
    assert r.status_code == 422
