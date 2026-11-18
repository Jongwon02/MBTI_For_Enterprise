"""수집 흐름(CLAUDE.md 12.7)과 관리자 API(docs/admin.md) 권한 테스트. MemoryStore로 운영 규칙을 흉내 낸다."""
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "api"))
sys.path.insert(0, str(ROOT / "api" / "engine" / "tests"))
sys.path.insert(0, str(ROOT / "api" / "tests"))

from bizdna_api import settings  # noqa: E402
from bizdna_api.main import app  # noqa: E402
from bizdna_api.store import MemoryStore, get_store  # noqa: E402
from fixtures import as_survey, case  # noqa: E402
from test_diagnoses import ALICE, BOB, SECRET, auth  # noqa: E402

ADMIN = "99999999-9999-9999-9999-999999999999"


@pytest.fixture()
def env(monkeypatch):
    monkeypatch.setattr(settings, "SUPABASE_JWT_SECRET", SECRET)
    store = MemoryStore()
    store.admins.add(ADMIN)
    store.consents[ALICE] = {"privacy", "storage", "analytics"}
    store.consents[BOB] = {"privacy", "storage"}  # 통계 동의 없음(이전 가입자)
    app.dependency_overrides[get_store] = lambda: store
    yield TestClient(app), store
    app.dependency_overrides.clear()


def complete(client, user, name="case_a", phase="full", did=None):
    body = {"survey": as_survey(case(name)), "complete": phase}
    if did:
        return client.put(f"/api/diagnoses/{did}", json=body, headers=auth(user)).json()
    return client.post("/api/diagnoses", json=body, headers=auth(user)).json()


# ---- 수집 ---------------------------------------------------------------------

def test_draft_creates_only_started_event(env):
    client, store = env
    client.post("/api/diagnoses", json={"survey": as_survey(case("case_a"))}, headers=auth(ALICE))
    assert store.facts == {} and [e["event"] for e in store.events] == ["started"]


def test_basic_then_full_is_one_row(env):
    client, store = env
    d = client.post("/api/diagnoses", json={"survey": as_survey(case("case_a"))}, headers=auth(ALICE)).json()
    complete(client, ALICE, phase="basic", did=d["id"])
    assert len(store.facts) == 1 and next(iter(store.facts.values()))["phase"] == "basic"
    complete(client, ALICE, phase="full", did=d["id"])
    complete(client, ALICE, phase="full", did=d["id"])  # 재저장해도 행·이벤트가 늘지 않는다
    assert len(store.facts) == 1
    f = next(iter(store.facts.values()))
    assert f["phase"] == "full" and f["round_no"] == 1 and len(f["domain_scores"]) == 8
    assert sorted(e["event"] for e in store.events) == ["basic_completed", "full_completed", "started"]


def test_round_no_increases_per_person(env):
    client, store = env
    complete(client, ALICE, "case_a")
    complete(client, ALICE, "case_b")
    assert sorted(f["round_no"] for f in store.facts.values()) == [1, 2]
    assert len({f["subject_key"] for f in store.facts.values()}) == 1


def test_full_save_counts_basic_too(env):
    client, store = env
    complete(client, ALICE, phase="full")
    assert sorted(e["event"] for e in store.events) == ["basic_completed", "full_completed", "started"]


def test_no_consent_no_collection(env):
    client, store = env
    complete(client, BOB)
    assert store.facts == {} and store.events == []


def test_rows_survive_diagnosis_delete(env):
    client, store = env
    d = complete(client, ALICE)
    assert client.delete(f"/api/diagnoses/{d['id']}", headers=auth(ALICE)).status_code == 204
    assert len(store.facts) == 1  # 2026-11-18 결정: 원본을 지워도 분석 행은 남는다


def test_fact_has_no_user_id(env):
    client, store = env
    complete(client, ALICE)
    f = next(iter(store.facts.values()))
    assert ALICE not in repr(f) and "그린푸드랩" not in repr(f)


# ---- 관리자 권한 -----------------------------------------------------------------

ADMIN_URLS = ["/api/admin/overview", "/api/admin/facts", "/api/admin/export.csv",
              "/api/admin/facts/00000000-0000-0000-0000-000000000000"]


@pytest.mark.parametrize("url", ADMIN_URLS)
def test_admin_requires_admin(env, url):
    client, _ = env
    assert client.get(url).status_code == 401
    assert client.get(url, headers=auth(ALICE)).status_code == 403


def test_me_reports_admin(env):
    client, _ = env
    assert client.get("/api/me", headers=auth(ADMIN)).json()["is_admin"] is True
    assert client.get("/api/me", headers=auth(ALICE)).json()["is_admin"] is False


def test_admin_overview_list_detail_export(env):
    client, store = env
    complete(client, ALICE, "case_a")
    complete(client, ALICE, "case_b")
    h = auth(ADMIN)

    ov = client.get("/api/admin/overview", headers=h).json()
    assert ov["n"] == 2 and ov["subjects"] == 1 and len(ov["axes"]) == 4

    page = client.get("/api/admin/facts?limit=1", headers=h).json()
    assert page["total"] == 2 and len(page["items"]) == 1
    item = page["items"][0]
    assert "diagnosis_id" not in item and "company_name" not in item
    assert item["top_strategies"] and item["dna_type"] in {"GICO", "GINO"}

    gico = client.get("/api/admin/facts?dna_type=GICO", headers=h).json()
    assert gico["total"] == 1 and gico["items"][0]["stage_code"] == "S3"
    assert client.get("/api/admin/facts?industry=서비스업", headers=h).json()["total"] == 0

    detail = client.get(f"/api/admin/facts/{item['fact_id']}", headers=h).json()
    assert len(detail["domain_scores"]) == 8 and len(detail["strategy_scores"]) == 12
    assert "diagnosis_id" not in detail

    csv = client.get("/api/admin/export.csv", headers=h)
    assert csv.status_code == 200 and csv.text.splitlines()[0].lstrip("﻿").startswith("fact_id,")
    assert len(csv.text.strip().splitlines()) == 3

    actions = [a["action"] for a in store.audit_logs]
    assert actions == ["admin.overview", "admin.facts", "admin.facts", "admin.facts", "admin.fact", "admin.export"]
    assert all(a["actor_id"] == ADMIN for a in store.audit_logs)


def test_admin_unknown_fact(env):
    client, _ = env
    h = auth(ADMIN)
    assert client.get("/api/admin/facts/not-a-uuid", headers=h).status_code == 404
    assert client.get("/api/admin/facts/00000000-0000-0000-0000-000000000000", headers=h).status_code == 404
