"""경영자 성향 데이터 수집(CLAUDE.md 12장). DB·HTTP에 의존하지 않는 순수 함수만 둔다.

- `derive_rows`: 최종저장한 진단 회차 1건 → 분석 행(팩트 1행, 역량 8행, 전략 12행).
  원본에서 **화이트리스트(12.5)에 있는 값만** 꺼낸다. 기업명·자유서술·회원 ID는 절대 넣지 않는다.
- `axis_direction`·`axis_score`: DNA 축 점수 ↔ 방향값(12.4).
- `summarize_facts`: 관리자 화면의 집계(docs/admin.md).
"""
from __future__ import annotations

import math
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

# 엔진 패키지(api/engine/bizdna). main.py를 거치지 않는 스크립트(migrate·backfill)에서도 불러오도록 경로를 잡는다.
_ENGINE = str(Path(__file__).resolve().parents[1] / "engine")
if _ENGINE not in sys.path:
    sys.path.insert(0, _ENGINE)

from bizdna import load_model, load_questions  # noqa: E402

AXIS_COLUMNS = {"G": "g", "I": "i", "N": "n", "P": "p"}  # 축의 A 성향 문자 → 컬럼 접미사
STAGE_INDICATORS = ("product", "customer", "revenue", "cash", "operations", "expansion")
DOMAINS = ("A", "B", "C", "D", "E", "F", "G", "H")
PLAN_CODE = re.compile(r"^P\d{2}$")


# ---- 12.4 DNA 방향값 --------------------------------------------------------------

def axis_direction(score: float | None) -> float | None:
    """축 점수(0~100) → 방향값(−100~+100). +는 A 성향(G·I·N·P), −는 B 성향."""
    return None if score is None else round((float(score) - 50) * 2, 2)


def axis_score(direction: float | None) -> float | None:
    """방향값 → 축 점수. axis_score(axis_direction(s)) == s 이어야 한다."""
    return None if direction is None else round(50 + float(direction) / 2, 2)


def direction_letter(direction: float | None, a: str, b: str, model: dict[str, Any]) -> str | None:
    """방향값 → 유형 문자. 기준값은 그 행의 모형 설정에서 읽는다(저장하지 않음)."""
    if direction is None:
        return None
    return a if direction >= (model["dna"]["letter_cutoff"] - 50) * 2 else b


def direction_boundary(direction: float | None, model: dict[str, Any]) -> bool | None:
    if direction is None:
        return None
    cfg = model["dna"]
    return (cfg["b_threshold"] - 50) * 2 < direction < (cfg["a_threshold"] - 50) * 2


# ---- 값 정리 (화이트리스트 안에서도 형식이 맞는 값만) -------------------------------------

def _num(v: Any) -> float | None:
    if isinstance(v, bool) or v is None or v == "":
        return None
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


def _int(v: Any) -> int | None:
    x = _num(v)
    return None if x is None else int(round(x))


def _choice(v: Any, options: list[str]) -> str | None:
    return v if isinstance(v, str) and v in options else None


def _choices(v: Any, options: list[str]) -> list[str]:
    if isinstance(v, str):
        v = [v]
    if not isinstance(v, list):
        return []
    return [x for x in v if isinstance(x, str) and x in options]


def _option_values(item: dict[str, Any]) -> list[str]:
    return [o if isinstance(o, str) else str(o.get("value")) for o in item.get("options", [])]


def model_for(version: str | None) -> dict[str, Any]:
    """회차의 모형 버전 설정. 지금은 model_v1 하나뿐이다. 버전이 늘면 이름 → 파일 대응을 여기에 둔다."""
    return load_model()


# ---- 12.5 화이트리스트로 분석 행 만들기 -----------------------------------------------

@dataclass
class AnalyticsRows:
    fact: dict[str, Any]
    domain_scores: list[dict[str, Any]] = field(default_factory=list)
    strategy_scores: list[dict[str, Any]] = field(default_factory=list)


def _company(survey: dict[str, Any], questions: dict[str, Any]) -> dict[str, Any]:
    raw = survey.get("company") or {}
    fields = {f["key"]: f for f in questions["company_fields"]}
    return {
        "industry": _choice(raw.get("industry"), fields["industry"].get("options", [])),
        "founded_year": _int(raw.get("founded_year")),
        "sales_recent": _num(raw.get("sales_recent")),
        "sales_prev": _num(raw.get("sales_prev")),
        "operating_margin": _num(raw.get("operating_margin")),
        "employees": _int(raw.get("employees")),
        "customer_type": _choices(raw.get("customer_type"), fields["customer_type"].get("options", [])),
    }


def _plan(answers: dict[str, Any], questions: dict[str, Any]) -> dict[str, Any]:
    """P문항 원값. 설정의 선택지·숫자 형식에 맞는 값만 남긴다(자유서술이 섞여 들어오지 않게)."""
    raw = answers.get("plan") or {}
    items = questions["plan"]["items"] if isinstance(questions["plan"], dict) else questions["plan"]
    out: dict[str, Any] = {}
    for item in items:
        code = item.get("code", "")
        if not PLAN_CODE.match(code) or code not in raw:
            continue
        kind = item.get("type")
        if kind == "multi":
            out[code] = _choices(raw[code], _option_values(item))
        elif kind == "single":
            v = _choice(raw[code], _option_values(item))
            if v is not None:
                out[code] = v
        elif kind == "number":
            v = _num(raw[code])
            if v is not None:
                out[code] = v
    return out


def derive_rows(diagnosis: dict[str, Any], *, subject_key: str, round_no: int) -> AnalyticsRows:
    """최종저장한 회차(public.diagnoses 행) → 분석 행. 가명키·회차 번호는 DB를 아는 호출자가 넘긴다."""
    result = diagnosis.get("result") or {}
    survey = diagnosis.get("survey") or {}
    answers = survey.get("answers") or {}
    model = model_for(diagnosis.get("model_version"))
    questions = load_questions()

    fact: dict[str, Any] = {
        "diagnosis_id": str(diagnosis["id"]),
        "model_version": diagnosis.get("model_version") or result.get("model_version"),
        "questions_version": diagnosis.get("questions_version") or result.get("questions_version"),
        "subject_key": str(subject_key),
        "round_no": int(round_no),
        "phase": diagnosis.get("phase") or "basic",
        "completed_at": diagnosis.get("completed_at"),
    } | _company(survey, questions)

    # 경영자 성향: 4축 방향값과 응답 수. 축 이름(한글)이 아니라 설정의 A 성향 문자로 컬럼을 고른다.
    dna = result.get("dna") or {}
    fact["dna_type"] = dna.get("type") if isinstance(dna.get("type"), str) else None
    for axis in (dna.get("axes") or {}).values():
        col = AXIS_COLUMNS.get(axis.get("a"))
        if col:
            fact[f"dna_{col}_dir"] = axis_direction(_num(axis.get("score")))
            fact[f"dna_{col}_answered"] = _int(axis.get("answered")) or 0
    for col in AXIS_COLUMNS.values():
        fact.setdefault(f"dna_{col}_dir", None)
        fact.setdefault(f"dna_{col}_answered", 0)

    # 성장단계: 6지표 원값(설문)과 엔진 판정
    stage_in = answers.get("stage") or {}
    for k in STAGE_INDICATORS:
        v = _int(stage_in.get(k))
        fact[f"stage_{k}"] = v if v is not None and 1 <= v <= 5 else None
    stage = result.get("stage") or {}
    fact |= {
        "stage_code": stage.get("code"),
        "stage_weighted_index": _num(stage.get("weighted_index")),
        "stage_provisional": stage.get("provisional"),
        "stage_gate_adjusted": stage.get("gate_adjusted") if isinstance(stage.get("gate_adjusted"), bool) else None,
        "stage_gates": [g["id"] for g in stage.get("gates_applied") or [] if isinstance(g, dict) and g.get("id")],
    }

    # 역량 요약 (정밀진단만)
    comp = result.get("competence") or None
    fact |= {
        "total_score": _num(comp.get("total")) if comp else None,
        "grade": ((comp.get("grade") or {}).get("grade")) if comp else None,
        "competence_missing_ratio": _num(comp.get("missing_ratio")) if comp else None,
    }

    # 성장계획·제약
    plan = _plan(answers, questions)
    fact["plan"] = plan
    fact["goals"] = [g for g in plan.get("P01", []) if g in model["goals"]]
    fact["risk_flags"] = [r for r in plan.get("P09", []) if r in model["risks"]]

    rows = AnalyticsRows(fact=fact)
    if comp:
        cfg = model["competence"]
        missing = [m for m in comp.get("missing") or [] if isinstance(m, str)]
        domains = comp.get("domains") or {}
        for d in DOMAINS:
            rows.domain_scores.append({
                "domain": d,
                "score": _num(domains.get(d)),
                "weight": cfg["domains"][d]["weight"],
                "answered": cfg["items_per_domain"] - sum(1 for m in missing if m.startswith(d)),
            })
        for rank, s in enumerate(result.get("strategies") or [], start=1):
            f = s.get("factors") or {}
            rows.strategy_scores.append({
                "strategy": s.get("code"),
                "fit": _num(f.get("fit")), "urgency": _num(f.get("urgency")),
                "impact": _num(f.get("impact")), "feasibility": _num(f.get("feasibility")),
                "total": _num(s.get("score")) or 0.0,
                "rank": rank,
                "status": s.get("status") if s.get("status") in ("recommended", "deferred") else "recommended",
                "rule_ids": [r for r in s.get("applied_rules") or [] if isinstance(r, str)],
            })
    return rows


# ---- 관리자 화면 집계 (docs/admin.md) ----------------------------------------------

def _quantiles(values: list[float]) -> dict[str, float | None]:
    xs = sorted(values)
    if not xs:
        return {"p25": None, "p50": None, "p75": None, "mean": None}

    def q(p: float) -> float:
        i = (len(xs) - 1) * p
        lo, hi = math.floor(i), math.ceil(i)
        return round(xs[lo] + (xs[hi] - xs[lo]) * (i - lo), 2)

    return {"p25": q(0.25), "p50": q(0.5), "p75": q(0.75), "mean": round(sum(xs) / len(xs), 2)}


def _counts(values: list[Any]) -> list[dict[str, Any]]:
    return [{"key": k, "n": n} for k, n in Counter(v for v in values if v is not None).most_common()]


def summarize_facts(facts: list[dict[str, Any]], events: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """팩트 행 목록 → 관리자 화면 집계. facts 행에는 `domains`({A: 점수})와 `top_strategies`(1~3순위)가 붙어 있다.

    관리자는 개별 행도 보는 내부 사용자이므로 표본 수 k 미만 숨김을 적용하지 않고 n을 함께 낸다.
    모형 버전이 섞이면 축 기준값은 각 행의 버전 설정으로 판정한다.
    """
    model = model_for(None)
    axes = model["dna"]["axes"]
    out: dict[str, Any] = {
        "n": len(facts),
        "subjects": len({f.get("subject_key") for f in facts}),
        "full": sum(1 for f in facts if f.get("phase") == "full"),
        "model_versions": _counts([f.get("model_version") for f in facts]),
        "dna_types": _counts([f.get("dna_type") for f in facts]),
        "stages": _counts([f.get("stage_code") for f in facts]),
        "industries": _counts([f.get("industry") for f in facts]),
        "grades": _counts([f.get("grade") for f in facts]),
        "risks": _counts([r for f in facts for r in f.get("risk_flags") or []]),
        "goals": _counts([g for f in facts for g in f.get("goals") or []]),
        "strategies": _counts([s for f in facts for s in (f.get("top_strategies") or [])[:3]]),
        "total_score": _quantiles([float(f["total_score"]) for f in facts if f.get("total_score") is not None]),
    }
    axis_rows = []
    for ax in axes:
        col = AXIS_COLUMNS[ax["a"]]
        dirs = [float(f[f"dna_{col}_dir"]) for f in facts if f.get(f"dna_{col}_dir") is not None]
        m = model
        axis_rows.append({
            "axis": ax["key"], "name": ax["name"], "a": ax["a"], "b": ax["b"],
            "a_name": ax["a_name"], "b_name": ax["b_name"],
            "n": len(dirs),
            "mean": round(sum(dirs) / len(dirs), 2) if dirs else None,
            "a_share": round(sum(1 for d in dirs if direction_letter(d, "A", "B", m) == "A") / len(dirs), 3) if dirs else None,
            "boundary_share": round(sum(1 for d in dirs if direction_boundary(d, m)) / len(dirs), 3) if dirs else None,
        })
    out["axes"] = axis_rows
    out["domains"] = [
        {"domain": d, "name": model["competence"]["domains"][d]["name"]}
        | _quantiles([float(f["domains"][d]) for f in facts if (f.get("domains") or {}).get(d) is not None])
        for d in DOMAINS
    ]
    ev = Counter(e.get("event") for e in events or [])
    out["funnel"] = {k: ev.get(k, 0) for k in ("started", "basic_completed", "full_completed")}
    out["labels"] = {
        "risks": model["risks"],
        "goals": {k: v["name"] for k, v in model["goals"].items()},
        "strategies": {k: v["name"] for k, v in model["strategy"]["library"].items()},
        "types": {k: (v["name"] if isinstance(v, dict) else v) for k, v in model["types"].items()},
        "stages": model["stage"]["names"],
    }
    return out


def iso(v: Any) -> Any:
    return v.isoformat() if isinstance(v, datetime) else v
