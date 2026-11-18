"""FR-01 회원가입(아이디 + 비밀번호, 이메일 인증 없음). Supabase 관리자 API 호출은 가짜로 바꿔 끼운다."""
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "api"))

from bizdna_api import settings, signup as signup_mod  # noqa: E402
from bizdna_api.main import app  # noqa: E402

client = TestClient(app)
OK = {"username": " Owner_01 ", "password": "abcd1234", "name": " 홍길동 ",
      "agree_privacy": True, "agree_storage": True, "agree_analytics": True, "terms_version": "v-test"}


@pytest.fixture()
def admin(monkeypatch):
    monkeypatch.setattr(settings, "SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setattr(settings, "SUPABASE_SECRET_KEY", "sb_secret_test")
    calls = []
    reply = {"status": 200, "body": {"id": "u-1"}}

    def fake(payload):
        calls.append(payload)
        return reply["status"], reply["body"]

    monkeypatch.setattr(signup_mod, "_admin_create_user", fake)
    return calls, reply


def test_creates_confirmed_user(admin):
    calls, _ = admin
    r = client.post("/api/auth/signup", json=OK)
    assert r.status_code == 201 and r.json() == {"id": "u-1", "username": "owner_01"}
    p = calls[0]
    assert p["email_confirm"] is True and p["email"] == "owner_01@users.bizdna.invalid"
    assert p["user_metadata"] == {"name": "홍길동", "username": "owner_01",
                                  "consents": {"privacy": "v-test", "storage": "v-test", "analytics": "v-test"}}


@pytest.mark.parametrize("change", [
    {"password": "short1"}, {"username": "abc"}, {"username": "a" * 21}, {"username": "1abcd"},
    {"username": "ab-cd"}, {"username": "me@example.com"}, {"username": "홍길동1234"},
    {"agree_privacy": False}, {"agree_storage": False}, {"agree_analytics": False},
])
def test_validation(admin, change):
    calls, _ = admin
    assert client.post("/api/auth/signup", json=OK | change).status_code == 422
    assert calls == []


@pytest.mark.parametrize("name", ["abcd", "a" * 20, "a_1_2"])
def test_username_boundaries(admin, name):
    assert client.post("/api/auth/signup", json=OK | {"username": name}).status_code == 201


def test_duplicate_username(admin):
    _, reply = admin
    reply.update(status=422, body={"error_code": "email_exists", "msg": "A user with this email address has already been registered"})
    r = client.post("/api/auth/signup", json=OK)
    assert r.status_code == 409 and "이미 사용 중" in r.json()["detail"]


def test_not_configured(monkeypatch):
    monkeypatch.setattr(settings, "SUPABASE_SECRET_KEY", "")
    assert client.post("/api/auth/signup", json=OK).status_code == 503
