"""소상공인 회원가입·진단 저장 API. 계정 분리(sosang/CLAUDE.md 3.4)와 본인 회차만 접근하는 권한 규칙을 확인한다."""
import sys
import time
from pathlib import Path

import jwt
import pytest
from fastapi.testclient import TestClient

API_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(API_DIR))
sys.path.insert(0, str(API_DIR / "engine" / "tests"))

from fixtures import case  # noqa: E402

from sosang_api import settings, signup as signup_mod  # noqa: E402
from sosang_api.main import app  # noqa: E402
from sosang_api.store import MemoryStore, get_store  # noqa: E402

SECRET = "test-secret-for-hs256-tokens-only-0123456789"
ALICE, BOB, SME = ("11111111-1111-1111-1111-111111111111", "22222222-2222-2222-2222-222222222222",
                   "33333333-3333-3333-3333-333333333333")


def token(sub: str, *, service: str | None = "sosang", secret: str = SECRET, role: str = "authenticated") -> str:
    claims = {"sub": sub, "role": role, "aud": "authenticated", "exp": int(time.time()) + 600,
              "app_metadata": {"provider": "email", **({"service": service} if service else {})}}
    return jwt.encode(claims, secret, algorithm="HS256")


def auth(sub: str, **kw) -> dict[str, str]:
    return {"Authorization": f"Bearer {token(sub, **kw)}"}


@pytest.fixture()
def store(monkeypatch):
    monkeypatch.setattr(settings, "SUPABASE_JWT_SECRET", SECRET)
    s = MemoryStore()
    s.members |= {ALICE, BOB}
    app.dependency_overrides[get_store] = lambda: s
    yield s
    app.dependency_overrides.clear()


@pytest.fixture()
def client(store):
    return TestClient(app)


def test_requires_login(client):
    assert client.get("/api/sosang/assessments").status_code == 401
    assert client.get("/api/sosang/assessments", headers={"Authorization": "Bearer nope"}).status_code == 401
    bad = token(ALICE, secret="wrong-secret-wrong-secret-wrong-secret!!")
    assert client.get("/api/sosang/assessments", headers={"Authorization": f"Bearer {bad}"}).status_code == 401
    assert client.get("/api/sosang/assessments", headers=auth(ALICE, role="anon")).status_code == 401


def test_rejects_sme_accounts(client, store):
    """중소경영 계정(app_metadata.service 없음)은 소상공인 API를 쓸 수 없다."""
    store.members.add(SME)  # 프로필이 있어도 서비스 표시가 없으면 거부
    assert client.get("/api/sosang/me", headers=auth(SME, service=None)).status_code == 403
    assert client.get("/api/sosang/assessments", headers=auth(SME, service="bizdna")).status_code == 403


def test_rejects_accounts_without_profile(client):
    """서비스 표시가 있어도 sosang.profiles에 행이 없으면 거부한다."""
    assert client.get("/api/sosang/me", headers=auth(SME)).status_code == 403
    assert client.get("/api/sosang/me", headers=auth(ALICE)).json() == {"id": ALICE}


def test_draft_then_final_save(client):
    survey = case("sample_cafe")
    r = client.post("/api/sosang/assessments", headers=auth(ALICE),
                    json={"survey": {**survey, "answers": {"dna": {}, "competence": {}, "special": {}}},
                          "progress": {"step": 2, "maxStep": 2, "percent": 10}})
    assert r.status_code == 201
    row = r.json()
    assert row["status"] == "draft" and row["result"] is None and row["store_name"] == survey["store"]["name"]

    r = client.put(f"/api/sosang/assessments/{row['id']}", headers=auth(ALICE),
                   json={"survey": survey, "progress": {"step": 7, "maxStep": 7, "percent": 100}, "complete": True})
    assert r.status_code == 200
    done = r.json()
    assert done["status"] == "completed" and done["completed_at"]
    assert done["result"]["dna"]["code"] == "GDRO" and done["result"]["competence"]["total"] == 48.75
    assert done["model_version"].startswith("sosang-") and done["questions_version"] and done["industries_version"]

    items = client.get("/api/sosang/assessments", headers=auth(ALICE)).json()
    assert len(items) == 1 and "survey" not in items[0]
    assert items[0]["summary"]["dna_type"] == "GDRO" and items[0]["summary"]["grade"] == "D"
    assert items[0]["summary"]["top_strategy"] == "수익구조 및 현금흐름 개선"


def test_other_members_cannot_access(client):
    row = client.post("/api/sosang/assessments", headers=auth(ALICE), json={"survey": case("sample_cafe")}).json()
    path = f"/api/sosang/assessments/{row['id']}"
    assert client.get(path, headers=auth(BOB)).status_code == 404
    assert client.put(path, headers=auth(BOB), json={"survey": {}}).status_code == 404
    assert client.delete(path, headers=auth(BOB)).status_code == 404
    assert client.get("/api/sosang/assessments", headers=auth(BOB)).json() == []
    assert client.delete(path, headers=auth(ALICE)).status_code == 204
    assert client.get(path, headers=auth(ALICE)).status_code == 404


def test_invalid_id_and_incomplete_final_save(client):
    assert client.get("/api/sosang/assessments/not-a-uuid", headers=auth(ALICE)).status_code == 404
    r = client.post("/api/sosang/assessments", headers=auth(ALICE), json={"survey": {"store": {}}, "complete": True})
    assert r.status_code == 422


def test_store_unconfigured_returns_503(monkeypatch):
    from sosang_api import store as store_mod

    monkeypatch.setattr(settings, "SUPABASE_JWT_SECRET", SECRET)
    monkeypatch.setattr(settings, "POSTGRES_URL", "")
    monkeypatch.setattr(store_mod, "_store", None)
    assert TestClient(app).get("/api/sosang/assessments", headers=auth(ALICE)).status_code == 503


# ---- 회원가입 ----------------------------------------------------------------
@pytest.fixture()
def signup_env(monkeypatch):
    calls = []
    monkeypatch.setattr(settings, "SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setattr(settings, "SUPABASE_SECRET_KEY", "sb_secret_test")
    monkeypatch.setattr(signup_mod, "_admin_create_user", lambda p: calls.append(p) or (200, {"id": ALICE}))
    return calls


BODY = {"username": "Cafe_Owner", "password": "password123", "name": "홍길동", "agree_privacy": True,
        "agree_storage": True, "terms_version": "sosang-2026-11-24-draft"}


def test_signup_marks_service_and_uses_sosang_domain(signup_env):
    r = TestClient(app).post("/api/sosang/auth/signup", json=BODY)
    assert r.status_code == 201 and r.json() == {"id": ALICE, "username": "cafe_owner"}
    p = signup_env[0]
    assert p["email"] == "cafe_owner@users.sosang.invalid"  # 중소경영(@users.bizdna.invalid)과 다른 도메인
    assert p["app_metadata"] == {"service": "sosang"} and p["email_confirm"] is True
    assert p["user_metadata"]["consents"] == {"privacy": BODY["terms_version"], "storage": BODY["terms_version"]}


@pytest.mark.parametrize("patch,status", [
    ({"username": "1abc"}, 422), ({"username": "ab"}, 422), ({"password": "short"}, 422),
    ({"agree_storage": False}, 422), ({"agree_privacy": False}, 422),
])
def test_signup_validation(signup_env, patch, status):
    assert TestClient(app).post("/api/sosang/auth/signup", json=BODY | patch).status_code == status
    assert signup_env == []


def test_signup_duplicate_and_unconfigured(monkeypatch, signup_env):
    monkeypatch.setattr(signup_mod, "_admin_create_user", lambda p: (422, {"error_code": "email_exists"}))
    assert TestClient(app).post("/api/sosang/auth/signup", json=BODY).status_code == 409
    monkeypatch.setattr(settings, "SUPABASE_SECRET_KEY", "")
    assert TestClient(app).post("/api/sosang/auth/signup", json=BODY).status_code == 503
