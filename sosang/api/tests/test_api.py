"""소상공인 API (게스트 진단) 테스트."""
import sys
from pathlib import Path

from fastapi.testclient import TestClient

API_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(API_DIR))
sys.path.insert(0, str(API_DIR / "engine" / "tests"))

from fixtures import case  # noqa: E402

from sosang_api.main import app  # noqa: E402

client = TestClient(app)


def test_health():
    assert client.get("/api/sosang/health").json() == {"status": "ok"}


def test_questions_have_items_and_no_scoring_values():
    body = client.get("/api/sosang/questions").json()
    q = body["questions"]
    assert len(q["dna"]) == 16 and len(q["competence"]) == 32 and len(q["special"]) == 36
    assert len(body["industries"]["majors"]) == 7 and len(body["industries"]["models"]) == 20
    assert "weights" not in body["model"] and "strategy" not in body["model"]


def test_diagnose_matches_engine_reference_case():
    r = client.post("/api/sosang/diagnose", json={"survey": case("sample_cafe")})
    assert r.status_code == 200
    body = r.json()
    assert body["dna"]["code"] == "GDRO" and body["competence"]["total"] == 48.75
    assert len(body["strategies"]["action_plan"]["items"]) == 3


def test_diagnose_invalid_input_is_422():
    survey = case("sample_cafe")
    survey["finance"]["monthly_sales"] = -1
    r = client.post("/api/sosang/diagnose", json={"survey": survey})
    assert r.status_code == 422 and "monthly_sales" in r.json()["detail"]


def test_report_pdf():
    r = client.post("/api/sosang/report", json={"survey": case("example_service_v4")})
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf" and r.content[:4] == b"%PDF"
    assert "filename*=UTF-8''" in r.headers["content-disposition"]


def test_report_without_competence_is_422():
    survey = case("sample_cafe")
    survey["answers"]["competence"] = {}
    assert client.post("/api/sosang/report", json={"survey": survey}).status_code == 422


def test_sme_routes_not_served():
    assert client.get("/api/questions").status_code == 404
