"""관리자 API: 경영자 성향 데이터 탐색(docs/admin.md).

- 모든 요청에서 DB(public.memberships의 role='admin')로 관리자인지 확인한다. user_metadata는 쓰지 않는다.
- 분석 저장소(analytics.*)의 가명 행만 보여준다. 기업명·아이디·원본 회차 ID는 응답에 없다.
- 조회·내보내기마다 private.audit_logs에 기록한다(CLAUDE.md 12.9).
"""
from __future__ import annotations

import csv
import io
import json
import uuid
from datetime import date, datetime, time, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response

from .analytics import summarize_facts
from .auth import User, current_user
from .store import DiagnosisStore, get_store

router = APIRouter(prefix="/api/admin")

# 목록·CSV에 보내는 열. 원값이지만 식별정보(기업명·자유서술·회원 ID)는 분석 저장소에 애초에 없다.
LIST_COLUMNS = (
    "fact_id", "subject_key", "round_no", "phase", "completed_at", "model_version", "industry", "founded_year",
    "sales_recent", "sales_prev", "operating_margin", "employees", "dna_type", "dna_g_dir", "dna_i_dir",
    "dna_n_dir", "dna_p_dir", "stage_code", "stage_weighted_index", "total_score", "grade", "goals", "risk_flags",
    "top_strategies",
)
PAGE_MAX = 200


def require_admin(user: User = Depends(current_user), store: DiagnosisStore = Depends(get_store)) -> User:
    if not store.is_admin(user.id):
        raise HTTPException(status_code=403, detail="관리자만 볼 수 있습니다.")
    return user


def _filters(industry: str | None = None, phase: str | None = None, stage: str | None = None,
             dna_type: str | None = None, model_version: str | None = None,
             since: date | None = None, until: date | None = None) -> dict[str, Any]:
    """since·until은 날짜(포함·미포함 아님: until 날짜 하루 전체를 포함한다)."""
    f: dict[str, Any] = {"industry": industry, "phase": phase, "stage": stage, "dna_type": dna_type,
                         "model_version": model_version}
    if since:
        f["since"] = datetime.combine(since, time.min, tzinfo=timezone.utc)
    if until:
        f["until"] = datetime.combine(until + timedelta(days=1), time.min, tzinfo=timezone.utc)
    return {k: v for k, v in f.items() if v}


def _log_filters(filters: dict[str, Any]) -> dict[str, Any]:
    return {k: (v.isoformat() if isinstance(v, datetime) else v) for k, v in filters.items()}


def _row(r: dict[str, Any]) -> dict[str, Any]:
    out = {k: r.get(k) for k in LIST_COLUMNS}
    if isinstance(out["completed_at"], datetime):
        out["completed_at"] = out["completed_at"].isoformat()
    return out


@router.get("/overview")
def overview(filters: dict[str, Any] = Depends(_filters), admin: User = Depends(require_admin),
             store: DiagnosisStore = Depends(get_store)) -> dict[str, Any]:
    facts = store.admin_facts(filters)
    summary = summarize_facts(facts, store.admin_funnel())
    store.audit(admin.id, "admin.overview", {"filters": _log_filters(filters), "n": summary["n"]})
    return summary | {"generated_at": datetime.now(timezone.utc).isoformat()}


@router.get("/facts")
def list_facts(filters: dict[str, Any] = Depends(_filters), offset: int = Query(0, ge=0),
               limit: int = Query(50, ge=1, le=PAGE_MAX), admin: User = Depends(require_admin),
               store: DiagnosisStore = Depends(get_store)) -> dict[str, Any]:
    rows = store.admin_facts(filters)
    page = rows[offset:offset + limit]
    store.audit(admin.id, "admin.facts", {"filters": _log_filters(filters), "offset": offset, "n": len(page)})
    return {"total": len(rows), "offset": offset, "limit": limit, "items": [_row(r) for r in page]}


@router.get("/facts/{fact_id}")
def get_fact(fact_id: str, admin: User = Depends(require_admin),
             store: DiagnosisStore = Depends(get_store)) -> dict[str, Any]:
    try:
        fid = str(uuid.UUID(fact_id))
    except ValueError as e:
        raise HTTPException(status_code=404, detail="회차를 찾을 수 없습니다.") from e
    row = store.admin_fact(fid)
    if not row:
        raise HTTPException(status_code=404, detail="회차를 찾을 수 없습니다.")
    store.audit(admin.id, "admin.fact", {"fact_id": fid})
    out = {k: v for k, v in row.items()}
    for k in ("completed_at", "created_at", "updated_at"):
        if isinstance(out.get(k), datetime):
            out[k] = out[k].isoformat()
    return out


@router.get("/export.csv")
def export_csv(filters: dict[str, Any] = Depends(_filters), admin: User = Depends(require_admin),
               store: DiagnosisStore = Depends(get_store)) -> Response:
    rows = [_row(r) for r in store.admin_facts(filters)]
    store.audit(admin.id, "admin.export", {"filters": _log_filters(filters), "n": len(rows)})
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=LIST_COLUMNS)
    w.writeheader()
    for r in rows:
        w.writerow({k: (json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v) for k, v in r.items()})
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    # 엑셀에서 한글이 깨지지 않도록 BOM을 붙인다.
    return Response("﻿" + buf.getvalue(), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": f'attachment; filename="bizdna_facts_{stamp}.csv"'})
