"""소상공인 진단 회차 저장소(sosang.assessments). 모든 메서드는 사용자 ID를 받아 **본인 회차만** 읽고 쓴다.

운영은 Supabase Postgres(PostgresStore), 테스트는 MemoryStore를 쓴다. 두 구현이 같은 규칙을 따른다.
중소경영 `public.diagnoses`와 섞이지 않게 테이블은 모두 `sosang` 스키마에 있다(sosang/CLAUDE.md 3.3).
`is_member`는 sosang.profiles에 행이 있는지 본다. 소상공인 가입 트리거가 만든 계정만 회원으로 인정한다(3.4).
"""
from __future__ import annotations

import copy
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Protocol
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from fastapi import HTTPException

from . import settings

SUMMARY_FIELDS = ("id", "store_name", "status", "progress", "model_version", "questions_version",
                  "industries_version", "created_at", "updated_at", "completed_at")
FIELDS = SUMMARY_FIELDS + ("survey", "result")
WRITABLE = {"store_name", "status", "survey", "progress", "result", "model_version", "questions_version",
            "industries_version", "completed_at"}


def summarize(row: dict[str, Any]) -> dict[str, Any]:
    """목록에는 설문 원본을 빼고 요약만 보낸다."""
    out = {k: row.get(k) for k in SUMMARY_FIELDS}
    r = row.get("result") or {}
    comp = r.get("competence") or {}
    top = ((r.get("strategies") or {}).get("items") or [None])[0]
    out["summary"] = {
        "dna_type": (r.get("dna") or {}).get("code"),
        "dna_name": (r.get("dna") or {}).get("name"),
        "total": comp.get("total"),
        "grade": (comp.get("grade") or {}).get("grade"),
        "sector_name": (r.get("store") or {}).get("sector_name"),
        "risks": len(r.get("risks") or []),
        "top_strategy": top.get("title") if top else None,
    } if r else None
    return out


class AssessmentStore(Protocol):
    def is_member(self, user_id: str) -> bool: ...
    def list(self, user_id: str) -> list[dict[str, Any]]: ...
    def get(self, user_id: str, assessment_id: str) -> dict[str, Any] | None: ...
    def create(self, user_id: str, data: dict[str, Any]) -> dict[str, Any]: ...
    def update(self, user_id: str, assessment_id: str, data: dict[str, Any]) -> dict[str, Any] | None: ...
    def delete(self, user_id: str, assessment_id: str) -> bool: ...


def _now() -> datetime:
    return datetime.now(timezone.utc)


class MemoryStore:
    """테스트용. 운영 저장소와 같은 권한 규칙(작성자 본인만)을 따른다."""

    def __init__(self) -> None:
        self.rows: dict[str, dict[str, Any]] = {}
        self.members: set[str] = set()  # 운영에서는 sosang.profiles

    def is_member(self, user_id: str) -> bool:
        return user_id in self.members

    def _own(self, user_id: str, assessment_id: str) -> dict[str, Any] | None:
        row = self.rows.get(assessment_id)
        return row if row and row["created_by"] == user_id else None

    def list(self, user_id: str) -> list[dict[str, Any]]:
        rows = [r for r in self.rows.values() if r["created_by"] == user_id]
        return [copy.deepcopy(r) for r in sorted(rows, key=lambda r: r["updated_at"], reverse=True)]

    def get(self, user_id: str, assessment_id: str) -> dict[str, Any] | None:
        row = self._own(user_id, assessment_id)
        return copy.deepcopy(row) if row else None

    def create(self, user_id: str, data: dict[str, Any]) -> dict[str, Any]:
        now = _now()
        row = {k: None for k in FIELDS} | {"status": "draft", "survey": {}, "progress": {}}
        row |= {k: copy.deepcopy(v) for k, v in data.items() if k in WRITABLE}
        row |= {"id": str(uuid.uuid4()), "created_by": user_id, "created_at": now, "updated_at": now}
        self.rows[row["id"]] = row
        return copy.deepcopy(row)

    def update(self, user_id: str, assessment_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        row = self._own(user_id, assessment_id)
        if not row:
            return None
        row |= {k: copy.deepcopy(v) for k, v in data.items() if k in WRITABLE}
        row["updated_at"] = _now()
        return copy.deepcopy(row)

    def delete(self, user_id: str, assessment_id: str) -> bool:
        return self.rows.pop(assessment_id, None) is not None if self._own(user_id, assessment_id) else False


def _clean_url(url: str) -> str:
    """Supabase 연동 URL에 붙는 비표준 쿼리(supa=...)는 libpq가 거부하므로 뺀다."""
    parts = urlsplit(url)
    keep = [(k, v) for k, v in parse_qsl(parts.query) if k in {"sslmode", "connect_timeout", "application_name"}]
    return urlunsplit(parts._replace(query=urlencode(keep)))


class PostgresStore:
    """Supabase Postgres. 서버리스이므로 요청마다 짧게 연결하고, 트랜잭션 풀러에 맞춰 prepared statement를 끈다."""

    def __init__(self, url: str) -> None:
        self.url = _clean_url(url)

    @contextmanager
    def _conn(self) -> Iterator[Any]:
        """한 번의 `with`가 한 트랜잭션이다. 끊긴 트랜잭션이 잠금을 오래 쥐지 않게 시간을 제한한다(중소경영 store와 같음)."""
        import psycopg
        from psycopg.rows import dict_row

        with psycopg.connect(self.url, prepare_threshold=None, row_factory=dict_row, connect_timeout=10) as c:
            c.execute("select set_config('lock_timeout', '5s', true),"
                      " set_config('idle_in_transaction_session_timeout', '20s', true),"
                      " set_config('statement_timeout', '20s', true)")
            yield c

    @staticmethod
    def _out(row: dict[str, Any] | None) -> dict[str, Any] | None:
        if row is None:
            return None
        row = dict(row)
        for k in ("id", "created_by"):
            if row.get(k) is not None:
                row[k] = str(row[k])
        return row

    @staticmethod
    def _values(data: dict[str, Any]) -> dict[str, Any]:
        from psycopg.types.json import Jsonb

        return {k: Jsonb(v) if k in {"survey", "progress", "result"} and v is not None else v
                for k, v in data.items() if k in WRITABLE}

    def is_member(self, user_id: str) -> bool:
        with self._conn() as c:
            return c.execute("select 1 from sosang.profiles where id = %s", (user_id,)).fetchone() is not None

    def list(self, user_id: str) -> list[dict[str, Any]]:
        with self._conn() as c:
            rows = c.execute(
                f"select created_by, result, {', '.join(SUMMARY_FIELDS)} from sosang.assessments"
                " where created_by = %s order by updated_at desc", (user_id,)).fetchall()
        return [self._out(r) for r in rows]  # type: ignore[misc]

    def get(self, user_id: str, assessment_id: str) -> dict[str, Any] | None:
        with self._conn() as c:
            row = c.execute("select * from sosang.assessments where id = %s and created_by = %s",
                            (assessment_id, user_id)).fetchone()
        return self._out(row)

    def create(self, user_id: str, data: dict[str, Any]) -> dict[str, Any]:
        vals = self._values(data) | {"created_by": user_id}
        cols = ", ".join(vals)
        marks = ", ".join(f"%({k})s" for k in vals)
        with self._conn() as c:
            row = c.execute(f"insert into sosang.assessments ({cols}) values ({marks}) returning *", vals).fetchone()
        return self._out(row)  # type: ignore[return-value]

    def update(self, user_id: str, assessment_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        vals = self._values(data)
        sets = ", ".join(f"{k} = %({k})s" for k in vals)
        sets = f"{sets}, updated_at = now()" if sets else "updated_at = now()"
        with self._conn() as c:
            row = c.execute(
                f"update sosang.assessments set {sets} where id = %(_id)s and created_by = %(_uid)s returning *",
                vals | {"_id": assessment_id, "_uid": user_id}).fetchone()
        return self._out(row)

    def delete(self, user_id: str, assessment_id: str) -> bool:
        with self._conn() as c:
            cur = c.execute("delete from sosang.assessments where id = %s and created_by = %s",
                            (assessment_id, user_id))
        return cur.rowcount > 0


_store: AssessmentStore | None = None


def get_store() -> AssessmentStore:
    """FastAPI 의존성. 테스트는 app.dependency_overrides로 MemoryStore를 넣는다."""
    global _store
    if _store is None:
        if not settings.POSTGRES_URL:
            raise HTTPException(status_code=503, detail="회원 저장 기능이 아직 설정되지 않았습니다. 게스트로 진단할 수 있습니다.")
        _store = PostgresStore(settings.POSTGRES_URL)
    return _store
