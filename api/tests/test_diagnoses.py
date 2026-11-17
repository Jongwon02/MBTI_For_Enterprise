"""FR-01·FR-12 회원 진단 저장 API. 토큰 검증과 본인 회차만 접근하는 권한 규칙을 확인한다."""
import sys
import time
from pathlib import Path

import jwt
import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "api"))
sys.path.insert(0, str(ROOT / "api" / "engine" / "tests"))

from bizdna_api import settings  # noqa: E402
from bizdna_api.main import app  # noqa: E402
from bizdna_api.store import MemoryStore, _clean_url, get_store  # noqa: E402
from fixtures import as_survey, case  # noqa: E402

SECRET = "test-secret-for-hs256-tokens-only-0123456789"
ALICE, BOB = "11111111-1111-1111-1111-111111111111", "22222222-2222-2222-2222-222222222222"


def token(sub: str, *, secret: str = SECRET, exp: int | None = None, role: str = "authenticated") -> str:
    claims = {"sub": sub, "role": role, "aud": "authenticated", "exp": exp or int(time.time()) + 600, "email": f"{sub[:4]}@test"}
    return jwt.encode(claims, secret, algorithm="HS256")


def auth(sub: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token(sub)}"}


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setattr(settings, "SUPABASE_JWT_SECRET", SECRET)
    store = MemoryStore()
    app.dependency_overrides[get_store] = lambda: store
    yield TestClient(app)
    app.dependency_overrides.clear()


def progress(**kw):
    return {"step": 3, "maxStep": 3, "basicDone": False, "phase": "basic"} | kw


def test_requires_login(client):
    assert client.get("/api/diagnoses").status_code == 401
    assert client.get("/api/diagnoses", headers={"Authorization": "Bearer nope"}).status_code == 401


def test_rejects_bad_tokens(client):
    bad = [token(ALICE, secret="wrong-secret-wrong-secret-wrong-secret!!"), token(ALICE, exp=int(time.time()) - 10),
           token(ALICE, role="anon")]
    for t in bad:
        assert client.get("/api/diagnoses", headers={"Authorization": f"Bearer {t}"}).status_code == 401
    none_alg = jwt.encode({"sub": ALICE, "role": "authenticated", "aud": "authenticated", "exp": int(time.time()) + 60},
                          None, algorithm="none")
    assert client.get("/api/diagnoses", headers={"Authorization": f"Bearer {none_alg}"}).status_code == 401


def test_me(client):
    assert client.get("/api/me", headers=auth(ALICE)).json()["id"] == ALICE


def test_draft_then_final_save(client):
    survey = as_survey(case("case_a"))
    r = client.post("/api/diagnoses", json={"survey": survey, "progress": progress()}, headers=auth(ALICE))
    assert r.status_code == 201
    d = r.json()
    assert d["status"] == "draft" and d["result"] is None and d["company_name"] == "그린푸드랩"

    # 기본진단 최종저장
    r = client.put(f"/api/diagnoses/{d['id']}", json={"survey": survey, "progress": progress(basicDone=True), "complete": "basic"},
                   headers=auth(ALICE))
    body = r.json()
    assert body["status"] == "basic_completed" and body["result"]["dna"]["type"] == "GICO"
    assert body["model_version"] and body["questions_version"] and body["completed_at"]

    # 정밀진단을 이어 하는 중간저장: 상태·결과 유지
    r = client.put(f"/api/diagnoses/{d['id']}", json={"survey": survey, "progress": progress(step=9, phase="full")}, headers=auth(ALICE))
    assert r.json()["status"] == "basic_completed" and r.json()["result"]["mode"] == "basic"

    # 정밀진단 최종저장
    r = client.put(f"/api/diagnoses/{d['id']}", json={"survey": survey, "progress": progress(phase="full"), "complete": "full"},
                   headers=auth(ALICE))
    body = r.json()
    assert body["status"] == "full_completed" and body["result"]["competence"]["total"] == 61.87

    # 이후 기본진단으로 다시 저장해도 정밀 완료 상태를 낮추지 않는다
    r = client.put(f"/api/diagnoses/{d['id']}", json={"survey": survey, "complete": "basic"}, headers=auth(ALICE))
    assert r.json()["status"] == "full_completed"

    items = client.get("/api/diagnoses", headers=auth(ALICE)).json()
    assert len(items) == 1 and "survey" not in items[0]
    assert items[0]["summary"]["dna_type"] == "GICO"


def test_other_users_cannot_access(client):
    d = client.post("/api/diagnoses", json={"survey": as_survey(case("case_a"))}, headers=auth(ALICE)).json()
    url = f"/api/diagnoses/{d['id']}"
    assert client.get(url, headers=auth(BOB)).status_code == 404
    assert client.put(url, json={"survey": {}}, headers=auth(BOB)).status_code == 404
    assert client.delete(url, headers=auth(BOB)).status_code == 404
    assert client.get("/api/diagnoses", headers=auth(BOB)).json() == []
    # 본인은 그대로 접근·삭제 가능
    assert client.get(url, headers=auth(ALICE)).status_code == 200
    assert client.delete(url, headers=auth(ALICE)).status_code == 204
    assert client.get(url, headers=auth(ALICE)).status_code == 404


def test_invalid_id_and_incomplete_final_save(client):
    assert client.get("/api/diagnoses/not-a-uuid", headers=auth(ALICE)).status_code == 404
    survey = as_survey(case("case_a"))
    survey["answers"]["stage"] = {}
    r = client.post("/api/diagnoses", json={"survey": survey, "complete": "basic"}, headers=auth(ALICE))
    assert r.status_code == 422


def test_store_unconfigured_returns_503(monkeypatch):
    monkeypatch.setattr(settings, "SUPABASE_JWT_SECRET", SECRET)
    monkeypatch.setattr(settings, "POSTGRES_URL", "")
    import bizdna_api.store as store_mod
    monkeypatch.setattr(store_mod, "_store", None)
    assert TestClient(app).get("/api/diagnoses", headers=auth(ALICE)).status_code == 503


def test_clean_url_drops_nonstandard_params():
    url = "postgres://u:p@host:6543/postgres?sslmode=require&supa=base-pooler.x"
    assert _clean_url(url) == "postgres://u:p@host:6543/postgres?sslmode=require"
