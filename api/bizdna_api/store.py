"""FR-12 진단 회차 저장소. 모든 메서드는 사용자 ID를 받아 **본인 회차만** 읽고 쓴다(서버측 권한 필터, CLAUDE.md 6장).

운영은 Supabase Postgres(PostgresStore), 테스트는 MemoryStore를 쓴다. 두 구현이 같은 규칙을 따른다.

경영자 성향 데이터 수집(CLAUDE.md 12.7): 통계 활용 동의가 있는 회원이 최종저장하면 **같은 트랜잭션에서**
analytics 스키마에 파생 행을 upsert한다. 회차를 지우거나 탈퇴해도 분석 행은 남긴다(2026-11-18 결정).
관리자 조회(docs/admin.md)는 `admin_*` 메서드로만 하고, 호출 전에 API가 관리자인지 확인한다.
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
from .analytics import derive_rows

COMPLETED = {"basic_completed", "full_completed"}
# 관리자 화면 필터. 키는 API 쿼리 이름, 값은 analytics.diagnosis_facts 컬럼.
ADMIN_FILTERS = {"industry": "industry", "phase": "phase", "stage": "stage_code", "dna_type": "dna_type",
                 "model_version": "model_version"}
# 관리자에게 보내지 않는 컬럼(원본 회차를 다시 만들 때만 쓰는 값, 12.5).
ADMIN_HIDDEN = {"diagnosis_id"}
# 집계·목록·CSV가 한 번에 읽는 최대 행 수. 전체 회차는 최대 약 5천 건으로 예상(2026-11-23)이고,
# 모형 버전을 올려 재계산하면 행이 버전 수만큼 늘어나므로 여유를 둔다. 넘으면 응답에 truncated를 표시한다.
ADMIN_ROW_LIMIT = 20000
# 같은 관리자가 같은 조건으로 다시 조회하면(자동 갱신 등) 이 시간 안에는 감사 로그를 한 번만 남긴다.
AUDIT_DEDUPE_SECONDS = 600


def _events_for(created: bool, data: dict[str, Any]) -> list[str]:
    """이번 저장으로 생기는 진행 이벤트. 새 회차면 started, 최종저장이면 그 완료 상태."""
    events = ["started"] if created else []
    if data.get("result") is not None and data.get("status") in COMPLETED:
        # 정밀 완료는 기본 완료를 거친 것이므로 함께 남긴다(이미 있으면 회차당 한 번만 기록됨).
        events += ["basic_completed", "full_completed"] if data["status"] == "full_completed" else ["basic_completed"]
    return events


def _insert_many(c: Any, table: str, cols: tuple[str, ...], rows: list[dict[str, Any]]) -> None:
    """같은 열의 여러 행을 INSERT 한 문장으로 넣는다. table·cols는 코드 상수만 넘긴다(사용자 입력 금지)."""
    if not rows:
        return
    values = ", ".join("(" + ", ".join(["%s"] * len(cols)) + ")" for _ in rows)
    c.execute(f"insert into {table} ({', '.join(cols)}) values {values}", [r[k] for r in rows for k in cols])


def _match(fact: dict[str, Any], filters: dict[str, Any]) -> bool:
    for key, col in ADMIN_FILTERS.items():
        if filters.get(key) and fact.get(col) != filters[key]:
            return False
    since, until = filters.get("since"), filters.get("until")
    at = fact.get("completed_at")
    if since and at and at < since:
        return False
    if until and at and at >= until:
        return False
    return True

# 목록에는 설문 원본을 빼고 요약만 보낸다.
SUMMARY_FIELDS = ("id", "company_name", "phase", "status", "progress", "model_version", "questions_version",
                  "created_at", "updated_at", "completed_at")
FIELDS = SUMMARY_FIELDS + ("survey", "result")
WRITABLE = {"company_name", "phase", "status", "survey", "progress", "result", "model_version",
            "questions_version", "completed_at"}


def summarize(row: dict[str, Any]) -> dict[str, Any]:
    out = {k: row.get(k) for k in SUMMARY_FIELDS}
    r = row.get("result") or {}
    out["summary"] = {
        "dna_type": (r.get("dna") or {}).get("type"),
        "dna_name": (r.get("dna") or {}).get("name"),
        "stage": (r.get("stage") or {}).get("code"),
        "stage_name": (r.get("stage") or {}).get("name"),
        "total": (r.get("competence") or {}).get("total"),
        "grade": ((r.get("competence") or {}).get("grade") or {}).get("grade"),
    } if r else None
    return out


class DiagnosisStore(Protocol):
    def list(self, user_id: str) -> list[dict[str, Any]]: ...
    def get(self, user_id: str, diagnosis_id: str) -> dict[str, Any] | None: ...
    def create(self, user_id: str, data: dict[str, Any]) -> dict[str, Any]: ...
    def update(self, user_id: str, diagnosis_id: str, data: dict[str, Any]) -> dict[str, Any] | None: ...
    def delete(self, user_id: str, diagnosis_id: str) -> bool: ...
    # 관리자 (docs/admin.md). API가 is_admin을 확인한 뒤에만 admin_*를 부른다.
    def is_admin(self, user_id: str) -> bool: ...
    def admin_facts(self, filters: dict[str, Any]) -> list[dict[str, Any]]: ...
    def admin_fact(self, fact_id: str) -> dict[str, Any] | None: ...
    def admin_funnel(self) -> list[dict[str, Any]]: ...
    def admin_model_versions(self) -> list[dict[str, Any]]: ...
    def audit(self, actor_id: str, action: str, detail: dict[str, Any], dedupe: bool = False) -> None: ...


def _now() -> datetime:
    return datetime.now(timezone.utc)


class MemoryStore:
    """테스트용. 운영 저장소와 같은 권한 규칙(작성자 본인만)을 따른다."""

    def __init__(self) -> None:
        self.rows: dict[str, dict[str, Any]] = {}
        # 수집·관리자 테스트용 (운영에서는 public.consents, public.memberships, private.*, analytics.*)
        self.consents: dict[str, set[str]] = {}
        self.admins: set[str] = set()
        self.subject_map: dict[str, str] = {}
        self.facts: dict[str, dict[str, Any]] = {}  # fact_id → 팩트 + domain_scores·strategy_scores
        self.events: list[dict[str, Any]] = []
        self.audit_logs: list[dict[str, Any]] = []

    def _collect(self, user_id: str, row: dict[str, Any], events: list[str]) -> None:
        if not events or "analytics" not in self.consents.get(user_id, set()):
            return
        sk = self.subject_map.setdefault(user_id, str(uuid.uuid4()))
        for ev in events:
            if not any(e["diagnosis_id"] == row["id"] and e["event"] == ev for e in self.events):
                self.events.append({"subject_key": sk, "diagnosis_id": row["id"], "event": ev, "occurred_at": _now()})
        if row.get("result") is None or row.get("status") not in COMPLETED or events == ["started"]:
            return
        same = [f for f in self.facts.values() if f["diagnosis_id"] == row["id"]]
        round_no = same[0]["round_no"] if same else 1 + max(
            (f["round_no"] for f in self.facts.values() if f["subject_key"] == sk), default=0)
        rows = derive_rows(row, subject_key=sk, round_no=round_no)
        old = next((f for f in same if f["model_version"] == rows.fact["model_version"]), None)
        fact_id = old["fact_id"] if old else str(uuid.uuid4())
        self.facts[fact_id] = copy.deepcopy(rows.fact) | {
            "fact_id": fact_id, "domain_scores": copy.deepcopy(rows.domain_scores),
            "strategy_scores": copy.deepcopy(rows.strategy_scores)}

    def _own(self, user_id: str, diagnosis_id: str) -> dict[str, Any] | None:
        row = self.rows.get(diagnosis_id)
        return row if row and row["created_by"] == user_id else None

    def list(self, user_id: str) -> list[dict[str, Any]]:
        rows = [r for r in self.rows.values() if r["created_by"] == user_id]
        return [copy.deepcopy(r) for r in sorted(rows, key=lambda r: r["updated_at"], reverse=True)]

    def get(self, user_id: str, diagnosis_id: str) -> dict[str, Any] | None:
        row = self._own(user_id, diagnosis_id)
        return copy.deepcopy(row) if row else None

    def create(self, user_id: str, data: dict[str, Any]) -> dict[str, Any]:
        now = _now()
        row = {k: None for k in FIELDS} | {"phase": "basic", "status": "draft", "survey": {}, "progress": {}}
        row |= {k: v for k, v in data.items() if k in WRITABLE}
        row |= {"id": str(uuid.uuid4()), "created_by": user_id, "created_at": now, "updated_at": now}
        self.rows[row["id"]] = row
        self._collect(user_id, row, _events_for(True, data))
        return copy.deepcopy(row)

    def update(self, user_id: str, diagnosis_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        row = self._own(user_id, diagnosis_id)
        if not row:
            return None
        row |= {k: v for k, v in data.items() if k in WRITABLE}
        row["updated_at"] = _now()
        self._collect(user_id, row, _events_for(False, data))
        return copy.deepcopy(row)

    def delete(self, user_id: str, diagnosis_id: str) -> bool:
        return self.rows.pop(diagnosis_id, None) is not None if self._own(user_id, diagnosis_id) else False

    def is_admin(self, user_id: str) -> bool:
        return user_id in self.admins

    @staticmethod
    def _admin_row(f: dict[str, Any]) -> dict[str, Any]:
        out = {k: v for k, v in f.items() if k not in ADMIN_HIDDEN | {"domain_scores", "strategy_scores"}}
        out["domains"] = {d["domain"]: d["score"] for d in f["domain_scores"]}
        out["top_strategies"] = [s["strategy"] for s in sorted(f["strategy_scores"], key=lambda s: s["rank"])
                                 if s["status"] == "recommended"][:3]
        return copy.deepcopy(out)

    def admin_facts(self, filters: dict[str, Any]) -> list[dict[str, Any]]:
        rows = [self._admin_row(f) for f in self.facts.values() if _match(f, filters)]
        return sorted(rows, key=lambda r: r["completed_at"], reverse=True)[:ADMIN_ROW_LIMIT]

    def admin_fact(self, fact_id: str) -> dict[str, Any] | None:
        f = self.facts.get(fact_id)
        if not f:
            return None
        return self._admin_row(f) | {"domain_scores": copy.deepcopy(f["domain_scores"]),
                                     "strategy_scores": copy.deepcopy(f["strategy_scores"])}

    def admin_funnel(self) -> list[dict[str, Any]]:
        return [{"event": e["event"]} for e in self.events]

    def admin_model_versions(self) -> list[dict[str, Any]]:
        counts: dict[str, int] = {}
        for f in self.facts.values():
            counts[f["model_version"]] = counts.get(f["model_version"], 0) + 1
        return [{"key": k, "n": n} for k, n in sorted(counts.items())]

    def audit(self, actor_id: str, action: str, detail: dict[str, Any], dedupe: bool = False) -> None:
        now = _now()
        if dedupe and any(a["actor_id"] == actor_id and a["action"] == action and a["detail"] == detail
                          and (now - a["at"]).total_seconds() < AUDIT_DEDUPE_SECONDS for a in self.audit_logs):
            return
        self.audit_logs.append({"actor_id": actor_id, "action": action, "detail": detail, "at": now})


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
        """한 번의 `with`가 한 트랜잭션이다(정상 종료 시 커밋, 예외 시 롤백).

        풀러 연결이 중간에 끊기면 DB 쪽 트랜잭션이 잠금을 쥔 채 남을 수 있다(2026-11-18 실제 발생).
        그래서 트랜잭션마다 잠금 대기·유휴 시간을 제한해 남은 트랜잭션이 스스로 정리되게 한다.
        세션 설정이 다른 요청으로 새지 않도록 set_config(..., true)로 이 트랜잭션에만 적용한다.
        """
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

    def list(self, user_id: str) -> list[dict[str, Any]]:
        with self._conn() as c:
            rows = c.execute(
                f"select created_by, result, {', '.join(SUMMARY_FIELDS)} from public.diagnoses"
                " where created_by = %s order by updated_at desc",
                (user_id,),
            ).fetchall()
        return [self._out(r) for r in rows]  # type: ignore[misc]

    def get(self, user_id: str, diagnosis_id: str) -> dict[str, Any] | None:
        with self._conn() as c:
            row = c.execute("select * from public.diagnoses where id = %s and created_by = %s",
                            (diagnosis_id, user_id)).fetchone()
        return self._out(row)

    @staticmethod
    def _values(data: dict[str, Any]) -> dict[str, Any]:
        from psycopg.types.json import Jsonb

        return {k: Jsonb(v) if k in {"survey", "progress", "result"} and v is not None else v
                for k, v in data.items() if k in WRITABLE}

    def create(self, user_id: str, data: dict[str, Any]) -> dict[str, Any]:
        vals = self._values(data) | {"created_by": user_id}
        cols = ", ".join(vals)
        marks = ", ".join(f"%({k})s" for k in vals)
        with self._conn() as c:  # 원본 저장과 분석 수집을 한 트랜잭션으로 묶는다(12.7)
            row = c.execute(f"insert into public.diagnoses ({cols}) values ({marks}) returning *", vals).fetchone()
            self._collect(c, user_id, row, _events_for(True, data))  # type: ignore[arg-type]
        return self._out(row)  # type: ignore[return-value]

    def update(self, user_id: str, diagnosis_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        vals = self._values(data)
        sets = ", ".join(f"{k} = %({k})s" for k in vals)
        sets = f"{sets}, updated_at = now()" if sets else "updated_at = now()"
        with self._conn() as c:
            row = c.execute(
                f"update public.diagnoses set {sets} where id = %(_id)s and created_by = %(_uid)s returning *",
                vals | {"_id": diagnosis_id, "_uid": user_id},
            ).fetchone()
            if row:
                self._collect(c, user_id, row, _events_for(False, data))
        return self._out(row)

    def delete(self, user_id: str, diagnosis_id: str) -> bool:
        # 분석 행(analytics.*)은 지우지 않는다(2026-11-18 결정, FK도 없음).
        with self._conn() as c:
            cur = c.execute("delete from public.diagnoses where id = %s and created_by = %s",
                            (diagnosis_id, user_id))
        return cur.rowcount > 0

    # ---- 경영자 성향 데이터 수집 (CLAUDE.md 12.7) ---------------------------------------
    def _collect(self, c: Any, user_id: str, row: dict[str, Any], events: list[str]) -> None:
        """통계 활용 동의가 있으면 이벤트와(최종저장이면) 분석 행을 쓴다. 호출자의 트랜잭션 안에서 실행된다."""
        from psycopg.types.json import Jsonb

        if not events:
            return
        consent = c.execute("select 1 from public.consents where user_id = %s and kind = 'analytics'"
                            " and withdrawn_at is null limit 1", (user_id,)).fetchone()
        if not consent:
            return
        sk = c.execute("select private.get_subject_key(%s) as k", (user_id,)).fetchone()["k"]
        for ev in events:
            c.execute("insert into analytics.funnel_events (subject_key, diagnosis_id, event) values (%s, %s, %s)"
                      " on conflict (diagnosis_id, event) do nothing", (sk, row["id"], ev))
        if row.get("result") is None or row.get("status") not in COMPLETED or events == ["started"]:
            return
        same = c.execute("select round_no from analytics.diagnosis_facts where diagnosis_id = %s limit 1",
                         (row["id"],)).fetchone()
        round_no = same["round_no"] if same else c.execute(
            "select coalesce(max(round_no), 0) + 1 as r from analytics.diagnosis_facts where subject_key = %s",
            (sk,)).fetchone()["r"]
        rows = derive_rows(row, subject_key=str(sk), round_no=round_no)
        fact = rows.fact | {"plan": Jsonb(rows.fact["plan"])}
        cols = list(fact)
        updates = ", ".join(f"{k} = excluded.{k}" for k in cols if k not in {"diagnosis_id", "model_version"})
        marks = ", ".join(f"%({k})s" for k in cols)
        fact_id = c.execute(
            f"insert into analytics.diagnosis_facts ({', '.join(cols)}) values ({marks})"
            f" on conflict (diagnosis_id, model_version) do update set {updates}, updated_at = now()"
            " returning fact_id", fact).fetchone()["fact_id"]
        c.execute("delete from analytics.domain_scores where fact_id = %s", (fact_id,))
        c.execute("delete from analytics.strategy_scores where fact_id = %s", (fact_id,))
        # 여러 행을 한 문장으로 넣어 DB 왕복을 줄인다(서버리스 + 원격 리전).
        _insert_many(c, "analytics.domain_scores", ("fact_id", "domain", "score", "weight", "answered"),
                     [d | {"fact_id": fact_id} for d in rows.domain_scores])
        _insert_many(c, "analytics.strategy_scores",
                     ("fact_id", "strategy", "fit", "urgency", "impact", "feasibility", "total", "rank", "status",
                      "rule_ids"),
                     [st | {"fact_id": fact_id} for st in rows.strategy_scores])

    # ---- 관리자 (docs/admin.md) ------------------------------------------------------
    def is_admin(self, user_id: str) -> bool:
        with self._conn() as c:
            return c.execute("select 1 from public.memberships where user_id = %s and role = 'admin'",
                             (user_id,)).fetchone() is not None

    _FACT_SELECT = (
        "select f.*,"
        " (select jsonb_object_agg(d.domain, d.score) from analytics.domain_scores d"
        "   where d.fact_id = f.fact_id) as domains,"
        " (select array_agg(t.strategy order by t.rank) from (select s.strategy, s.rank"
        "   from analytics.strategy_scores s where s.fact_id = f.fact_id and s.status = 'recommended'"
        "   order by s.rank limit 3) t) as top_strategies"
        " from analytics.diagnosis_facts f")

    @staticmethod
    def _plain(row: dict[str, Any]) -> dict[str, Any]:
        """UUID·Decimal을 JSON으로 보낼 수 있는 값으로 바꾼다."""
        from decimal import Decimal

        out = {}
        for k, v in row.items():
            if isinstance(v, uuid.UUID):
                v = str(v)
            elif isinstance(v, Decimal):
                v = float(v)
            out[k] = v
        return out

    def _admin_out(self, row: dict[str, Any]) -> dict[str, Any]:
        out = {k: v for k, v in self._plain(row).items() if k not in ADMIN_HIDDEN}
        out["domains"] = {k: (float(v) if v is not None else None) for k, v in (row.get("domains") or {}).items()}
        out["top_strategies"] = row.get("top_strategies") or []
        return out

    def admin_facts(self, filters: dict[str, Any]) -> list[dict[str, Any]]:
        where, args = [], {}
        for key, col in ADMIN_FILTERS.items():
            if filters.get(key):
                where.append(f"f.{col} = %({key})s")
                args[key] = filters[key]
        if filters.get("since"):
            where.append("f.completed_at >= %(since)s")
            args["since"] = filters["since"]
        if filters.get("until"):
            where.append("f.completed_at < %(until)s")
            args["until"] = filters["until"]
        sql = self._FACT_SELECT + (" where " + " and ".join(where) if where else "")
        sql += f" order by f.completed_at desc limit {ADMIN_ROW_LIMIT}"
        with self._conn() as c:
            return [self._admin_out(r) for r in c.execute(sql, args).fetchall()]

    def admin_fact(self, fact_id: str) -> dict[str, Any] | None:
        with self._conn() as c:
            row = c.execute(self._FACT_SELECT + " where f.fact_id = %s", (fact_id,)).fetchone()
            if not row:
                return None
            out = self._admin_out(row)
            out["domain_scores"] = [self._plain(r) for r in c.execute(
                "select domain, score, weight, answered from analytics.domain_scores"
                " where fact_id = %s order by domain", (fact_id,)).fetchall()]
            out["strategy_scores"] = [self._plain(r) for r in c.execute(
                "select strategy, fit, urgency, impact, feasibility, total, rank, status, rule_ids"
                " from analytics.strategy_scores where fact_id = %s order by rank", (fact_id,)).fetchall()]
        return out

    def admin_funnel(self) -> list[dict[str, Any]]:
        with self._conn() as c:
            return [dict(r) for r in c.execute("select event from analytics.funnel_events").fetchall()]

    def admin_model_versions(self) -> list[dict[str, Any]]:
        with self._conn() as c:
            return [{"key": r["model_version"], "n": r["n"]} for r in c.execute(
                "select model_version, count(*)::int as n from analytics.diagnosis_facts"
                " group by model_version order by model_version").fetchall()]

    def audit(self, actor_id: str, action: str, detail: dict[str, Any], dedupe: bool = False) -> None:
        from psycopg.types.json import Jsonb

        with self._conn() as c:
            if not dedupe:
                c.execute("insert into private.audit_logs (actor_id, action, detail) values (%s, %s, %s)",
                          (actor_id, action, Jsonb(detail)))
                return
            # 같은 관리자·동작·조건(detail)이 최근 AUDIT_DEDUPE_SECONDS 안에 있으면 남기지 않는다.
            c.execute("insert into private.audit_logs (actor_id, action, detail)"
                      " select %(a)s, %(act)s, %(d)s where not exists (select 1 from private.audit_logs"
                      "  where actor_id = %(a)s and action = %(act)s and detail = %(d)s"
                      "    and at > now() - make_interval(secs => %(s)s))",
                      {"a": actor_id, "act": action, "d": Jsonb(detail), "s": AUDIT_DEDUPE_SECONDS})


_store: DiagnosisStore | None = None


def get_store() -> DiagnosisStore:
    """FastAPI 의존성. 테스트는 app.dependency_overrides로 MemoryStore를 넣는다."""
    global _store
    if _store is None:
        if not settings.POSTGRES_URL:
            raise HTTPException(status_code=503, detail="회원 저장 기능이 아직 설정되지 않았습니다. 게스트로 진단할 수 있습니다.")
        _store = PostgresStore(settings.POSTGRES_URL)
    return _store
