"""Biz-DNA 소상공인 진단엔진 v1.

DB·HTTP에 의존하지 않는 순수 함수다. legacy/mvp_v4의 계산(engine.diagnose → advanced.diagnose_v4)을
그대로 재현하고, sosang/CLAUDE.md에 따라 다음을 바꿨다.
- 미응답은 오류가 아니라 결측(None)이다. 응답한 문항만으로 점수를 내고, 영역 전체가 결측이면
  그 영역을 빼고 가중치를 다시 나눈다.
- 비용을 항목별(원재료·매입비, 인건비, 임대료, 기타)로 받고 합계를 계산한다.
- 종합점수에 A~E 등급을 붙이고, 전략마다 적용된 규칙 ID를 남긴다.
- 결과에 모형·문항·업종분류 버전을 기록한다.
- v4는 특화점수 반영 뒤 우선점수를 다시 계산할 때 적자 시 재무·수익 시급성 하한(95)을 빠뜨렸다.
  CLAUDE.md 4.6 규칙대로 재계산에도 하한을 적용한다(설정 `reapply_deficit_floor`, false면 v4와 같다.
  기준 사례 4개는 흑자라 영향 없음).
"""
from __future__ import annotations

from math import isfinite
from typing import Any

from .config import load_industries, load_model, load_questions


class DiagnosticError(ValueError):
    """입력 형식이 잘못됐을 때. 미응답은 오류가 아니다."""


# ---------------------------------------------------------------- 공통 도우미

def _likert(value: Any, label: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not 1 <= value <= 5:
        raise DiagnosticError(f"{label}: 1~5 범위 숫자가 필요합니다")
    return float(value)


def _amount(value: Any, label: str, *, required: bool = False) -> float | None:
    if value is None or value == "":
        if required:
            raise DiagnosticError(f"{label}: 값이 필요합니다")
        return None
    if isinstance(value, bool):
        raise DiagnosticError(f"{label}: 숫자가 필요합니다")
    try:
        v = float(value)
    except (TypeError, ValueError):
        raise DiagnosticError(f"{label}: 숫자가 필요합니다") from None
    if not isfinite(v) or v < 0:
        raise DiagnosticError(f"{label}: 0 이상의 유한한 숫자가 필요합니다")
    return v


def _scale(values: list[float]) -> float:
    """1~5점 응답을 0~100점으로 환산한다: Σ(x−1) / (4n) × 100."""
    return round(sum(x - 1 for x in values) / (4 * len(values)) * 100, 2)


def _collect(codes: list[str], answers: dict[str, Any], reverse: set[str], ns: str) -> tuple[list[float], list[str]]:
    values: list[float] = []
    missing: list[str] = []
    for code in codes:
        x = _likert(answers.get(code), f"{ns}.{code}")
        if x is None:
            missing.append(code)
        else:
            values.append(6 - x if code in reverse else x)
    return values, missing


def grade_for(total: float, model: dict[str, Any]) -> dict[str, str]:
    for g in model["competence"]["grades"]:
        if total >= g["min"]:
            return {"grade": g["grade"], "name": g["name"]}
    raise AssertionError("grades must cover 0")


def resolve_sector_group(store: dict[str, Any], model: dict[str, Any], industries: dict[str, Any]) -> str:
    """점포의 업종 정보를 엔진 v1의 업종 4종(food·retail·life·other) 중 하나로 정한다."""
    groups = model["sector_groups"]
    explicit = store.get("sector_group")
    if explicit is not None:
        if explicit not in groups:
            raise DiagnosticError(f"store.sector_group: {sorted(groups)} 중 하나여야 합니다")
        return explicit
    major = store.get("major")
    if major is None and store.get("biz_model"):
        major = next((m["major"] for m in industries["models"] if m["code"] == store["biz_model"]), None)
    if major is None:
        return "other"
    found = next((m for m in industries["majors"] if m["code"] == major), None)
    if found is None:
        raise DiagnosticError(f"store.major: 알 수 없는 대분류 {major}")
    return found["sector_group"]


# ---------------------------------------------------------------- DNA

def _diagnose_dna(answers: dict[str, Any], model: dict[str, Any], reverse: set[str]) -> dict[str, Any]:
    cfg = model["dna"]
    axes: list[dict[str, Any]] = []
    code = ""
    missing_all: list[str] = []
    for axis in cfg["axes"]:
        values, missing = _collect(axis["items"], answers, reverse, "dna")
        missing_all += missing
        if not values:
            axes.append({"key": axis["key"], "name": axis["name"], "score": None, "letter": None,
                         "lean": None, "boundary": None, "answered": 0})
            code += "?"
            continue
        score = _scale(values)
        letter = axis["a"] if score >= cfg["letter_cutoff"] else axis["b"]
        code += letter
        if score >= cfg["a_threshold"]:
            lean = axis["a_name"]
        elif score <= cfg["b_threshold"]:
            lean = axis["b_name"]
        else:
            lean = "경계"
        axes.append({
            "key": axis["key"], "name": axis["name"], "score": score, "letter": letter, "lean": lean,
            "boundary": cfg["b_threshold"] < score < cfg["a_threshold"], "answered": len(values),
            "a": axis["a"], "b": axis["b"], "a_name": axis["a_name"], "b_name": axis["b_name"],
        })
    type_info = model["types"].get(code)
    return {
        "code": code if type_info else None,
        "name": type_info["name"] if type_info else None,
        "strategy": type_info["strategy"] if type_info else None,
        "axes": axes,
        "boundary_axes": [a["key"] for a in axes if a["boundary"]],
        "provisional": any(a["boundary"] for a in axes),
        "missing": missing_all,
        "notice": cfg["notice"],
    }


# ---------------------------------------------------------------- 8대 역량

def _diagnose_competence(answers: dict[str, Any], special: dict[str, Any], sector: str,
                         model: dict[str, Any], questions: dict[str, Any], reverse: set[str]) -> dict[str, Any]:
    comp = model["competence"]
    weights = comp["weights"].get(sector, comp["weights"]["default"])
    blend = comp["special_blend"]
    by_area: dict[str, list[str]] = {}
    for q in questions["competence"]:
        by_area.setdefault(q["area"], []).append(q["code"])
    special_by_area: dict[str, list[str]] = {}
    for q in questions["special"]:
        if q["sector"] == sector:
            special_by_area.setdefault(q["area"], []).append(q["code"])

    areas: list[dict[str, Any]] = []
    missing_total = 0
    item_total = 0
    for a in comp["areas"]:
        codes = by_area[a["code"]]
        values, missing = _collect(codes, answers, reverse, "competence")
        item_total += len(codes)
        missing_total += len(missing)
        common = _scale(values) if values else None
        special_score = None
        special_missing: list[str] = []
        if a["code"] in special_by_area:
            s_values, special_missing = _collect(special_by_area[a["code"]], special, reverse, "special")
            special_score = _scale(s_values) if s_values else None
        if common is None:
            score = None
        elif special_score is not None:
            score = round((1 - blend) * common + blend * special_score, 2)
        else:
            score = common
        areas.append({
            "code": a["code"], "name": a["name"], "detail": a["detail"], "weight": weights[a["code"]],
            "common_score": common, "special_score": special_score, "score": score,
            "answered": len(values), "missing": missing, "special_missing": special_missing,
        })

    present = [a for a in areas if a["score"] is not None]
    total = grade = None
    if present:
        w_sum = sum(a["weight"] for a in present)
        total = round(sum(a["score"] * a["weight"] for a in present) / w_sum, 2)
        grade = grade_for(total, model)
    order = sorted(present, key=lambda a: -a["score"])  # 안정 정렬: 같은 점수는 영역 순서(A→H)
    return {
        "areas": areas,
        "weights": weights,
        "total": total,
        "grade": grade,
        "strengths": [a["code"] for a in order[:2]],
        "weaknesses": [a["code"] for a in sorted(present, key=lambda a: a["score"])[:2]],
        "excluded_areas": [a["code"] for a in areas if a["score"] is None],
        "missing_ratio": round(missing_total / item_total, 4) if item_total else 0.0,
        "special_areas": [a["code"] for a in areas if a["special_score"] is not None],
    }


# ---------------------------------------------------------------- 재무·위험

def _finance(finance: dict[str, Any]) -> dict[str, Any]:
    sales = _amount(finance.get("monthly_sales"), "finance.monthly_sales", required=True)
    items = {k: _amount(finance.get(k), f"finance.{k}") for k in ("material_cost", "labor_cost", "rent", "other_cost")}
    costs = {k: (v or 0.0) for k, v in items.items()}
    total_cost = sum(costs.values())
    residual = sales - total_cost

    def ratio(x: float) -> float | None:
        return round(x / sales * 100, 2) if sales else None

    return {
        "monthly_sales": sales, **costs, "total_cost": round(total_cost, 2),
        "unanswered_costs": [k for k, v in items.items() if v is None],
        "operating_residual": round(residual, 2),
        "residual_margin_pct": ratio(residual),
        "rent_ratio_pct": ratio(costs["rent"]),
        "material_ratio_pct": ratio(costs["material_cost"]),
        "labor_ratio_pct": ratio(costs["labor_cost"]),
        "cost_ratio_pct": ratio(total_cost),
    }


def _risks(fin: dict[str, Any], comp: dict[str, Any], growth_pct: float | None, model: dict[str, Any]) -> list[dict[str, Any]]:
    cfg = model["risks"]
    sales, cost, residual = fin["monthly_sales"], fin["total_cost"], fin["operating_residual"]
    finance_score = next(a["score"] for a in comp["areas"] if a["code"] == "E")
    hits: list[str] = []
    if sales == 0:
        hits.append("NO_SALES")
    if residual < 0:
        hits.append("NEGATIVE_CASH")
    if sales and fin["rent_ratio_pct"] > cfg["rent_ratio_pct"]:
        hits.append("RENT_BURDEN")
    if sales > 0 and cost > sales * cfg["low_buffer_cost_ratio"]:
        hits.append("LOW_BUFFER")
    if finance_score is not None and finance_score < cfg["weak_finance_score"]:
        hits.append("WEAK_FINANCE")
    if cfg["sales_decline_pct"] is not None and growth_pct is not None and growth_pct <= -cfg["sales_decline_pct"]:
        hits.append("SALES_DECLINE")
    return [{"code": c, "level": cfg["levels"][c], "text": cfg["texts"][c]} for c in hits]


# ---------------------------------------------------------------- 전략 (임시 규칙, v4 재현)

def _strategies(comp: dict[str, Any], fin: dict[str, Any], sector: str, goal: str, model: dict[str, Any]) -> dict[str, Any]:
    cfg = model["strategy"]
    rules = cfg["rules"]
    w = cfg["weights"]
    deficit = fin["operating_residual"] < 0
    rent_ratio = fin["rent_ratio_pct"]
    goal_area = model["goals"]["items"][goal]["area"]
    bonus = cfg["sector_bonus"].get(sector, {})

    def priority(urgency: float, fit: float, feas: float) -> float:
        return round(w["urgency"] * urgency + w["fit"] * fit + w["feasibility"] * feas, 2)

    rows = []
    for a in comp["areas"]:
        if a["score"] is None:
            continue
        code = a["code"]
        applied: list[str] = []
        urgency = 100 - a["common_score"]
        fit: float = cfg["fit_base"] + bonus.get(code, 0) * cfg["fit_bonus_multiplier"]
        if bonus.get(code):
            applied.append("SECTOR_BONUS")
        if code == "E" and deficit:
            fit = rules["deficit_finance_fit"]
            urgency = max(urgency, rules["deficit_finance_min_urgency"])
            applied.append("DEFICIT_FINANCE_FIRST")
        if code == "E" and rent_ratio is not None and rent_ratio > model["risks"]["rent_ratio_pct"]:
            fit = min(100, fit + rules["rent_burden_finance_fit_add"])
            applied.append("RENT_BURDEN_FINANCE")
        if code == "D" and deficit:
            fit = rules["deficit_marketing_fit"]
            applied.append("DEFICIT_MARKETING_FIT")
        if code == "F" and sector == "food":
            fit += rules["food_operation_fit_add"]
            applied.append("FOOD_OPERATION")
        if code == goal_area:
            fit = min(100, fit + rules["goal_fit_add"])
            applied.append(f"GOAL_{goal.upper()}")
        feas = cfg["feasibility"].get(code, cfg["feasibility"]["default"])
        gated = deficit and code in rules["deficit_gate_areas"]
        p = priority(urgency, fit, feas)
        if gated:
            p = min(p, rules["deficit_gate_cap"])
            applied.append("DEFICIT_GATE")
        rows.append({"area": a, "fit": fit, "feasibility": feas, "gated": gated, "rules": applied, "priority": p})

    # 1차: 공통점수 기준 정렬 후 상위 N개 (v4: 같은 점수면 영역명 순)
    rows.sort(key=lambda r: (-r["priority"], r["area"]["name"]))
    shortlist = rows[: cfg["shortlist"]]

    # 2차: 특화점수 반영 점수로 시급성·우선점수 재계산 후 안정 정렬 (v4 동작)
    for r in shortlist:
        a = r["area"]
        gap = round(100 - a["score"], 2)
        if a["code"] == "E" and deficit and rules["reapply_deficit_floor"]:
            gap = max(gap, rules["deficit_finance_min_urgency"])
        r["urgency"] = gap
        r["priority"] = priority(gap, r["fit"], r["feasibility"])
        if r["gated"]:
            r["priority"] = min(r["priority"], rules["deficit_gate_cap"])
    shortlist.sort(key=lambda r: -r["priority"])

    items = []
    for rank, r in enumerate(shortlist, start=1):
        a = r["area"]
        info = cfg["items"][a["code"]]
        rationale = (f"역량 {a['score']:.1f}점, 격차 {r['urgency']:.1f}점, "
                     f"적합도 {r['fit']:.0f}점, 실행가능성 {r['feasibility']:.0f}점")
        if r["gated"]:
            rationale += "; 적자상태로 확장성 지출 우선순위 제한"
        items.append({
            "rank": rank, "area": a["code"], "area_name": a["name"], **info,
            "priority": r["priority"], "urgency": r["urgency"], "fit": r["fit"],
            "feasibility": r["feasibility"], "gated": r["gated"], "rules": r["rules"],
            "rationale": rationale,
        })
    plans = model["action_plans"]
    action_plan = {
        "draft": plans["draft"],
        "items": [{"rank": s["rank"], "area": s["area"], "title": s["title"], "kpi": s["kpi"],
                   **plans["items"][s["area"]]} for s in items[: cfg["top"]]],
    }
    return {"provisional": cfg["provisional"], "notice": cfg["notice"], "items": items,
            "top": items[: cfg["top"]], "goal": goal, "goal_area": goal_area, "action_plan": action_plan}


# ---------------------------------------------------------------- 성장단계·신뢰도

OBS_KEYS = ("sales_prev", "repeat_rate", "months_operating", "channels", "staff", "positive_cashflow_months")


def _observations(obs: dict[str, Any]) -> dict[str, float]:
    clean = {}
    for k in OBS_KEYS:
        v = _amount(obs.get(k), f"observations.{k}")
        if v is not None:
            clean[k] = v
    if clean.get("repeat_rate", 0) > 100:
        raise DiagnosticError("observations.repeat_rate: 0~100(%) 범위여야 합니다")
    if clean.get("positive_cashflow_months", 0) > 12:
        raise DiagnosticError("observations.positive_cashflow_months: 0~12 범위여야 합니다")
    return clean


def _stage(clean: dict[str, float], growth: float | None, model: dict[str, Any]) -> dict[str, Any]:
    cfg = model["stage"]
    labels = cfg["labels"]
    if not all(k in clean for k in ("months_operating", "repeat_rate", "positive_cashflow_months")):
        return {"code": "UNDETERMINED", "label": labels["UNDETERMINED"], "reason": cfg["undetermined_note"]}
    months, repeat, positive = clean["months_operating"], clean["repeat_rate"], clean["positive_cashflow_months"]
    if months < cfg["s1"]["months_lt"] or repeat < cfg["s1"]["repeat_lt"]:
        code = "S1"
    elif months < cfg["s2"]["months_lt"] or repeat < cfg["s2"]["repeat_lt"]:
        code = "S2"
    elif positive < cfg["s3"]["positive_months_lt"] or growth is None:
        code = "S3"
    elif (growth >= cfg["s4"]["growth_pct_gte"] and clean.get("channels", 0) >= cfg["s4"]["channels_gte"]
          and clean.get("staff", 0) >= cfg["s4"]["staff_gte"]):
        code = "S4"
    else:
        code = "S3"
    return {"code": code, "label": labels[code], "reason": cfg["rules_note"]}


# ---------------------------------------------------------------- 진입점

def diagnose(payload: dict[str, Any], *, model_name: str = "model_v1", questions_name: str = "questions_v1",
             industries_name: str = "industries_v1") -> dict[str, Any]:
    """진단 입력(payload)으로 결과를 만든다. 같은 입력·같은 버전이면 항상 같은 결과다."""
    model = load_model(model_name)
    questions = load_questions(questions_name)
    industries = load_industries(industries_name)
    if not isinstance(payload, dict):
        raise DiagnosticError("payload는 객체여야 합니다")
    store = payload.get("store") or {}
    answers = payload.get("answers") or {}
    reverse = set(questions["reverse_items"])

    sector = resolve_sector_group(store, model, industries)
    goal = store.get("goal") or model["goals"]["default"]
    if goal not in model["goals"]["items"]:
        raise DiagnosticError(f"store.goal: {sorted(model['goals']['items'])} 중 하나여야 합니다")

    dna = _diagnose_dna(answers.get("dna") or {}, model, reverse)
    comp = _diagnose_competence(answers.get("competence") or {}, answers.get("special") or {},
                                sector, model, questions, reverse)
    fin = _finance(payload.get("finance") or {})

    clean = _observations(payload.get("observations") or {})
    growth = None
    if "sales_prev" in clean and clean["sales_prev"] > 0:
        growth = round((fin["monthly_sales"] / clean["sales_prev"] - 1) * 100, 2)
    stage = _stage(clean, growth, model)

    benchmark = None
    if payload.get("benchmark"):
        b = payload["benchmark"]
        val = _amount(b.get("monthly_sales"), "benchmark.monthly_sales", required=True)
        benchmark = {"source": b.get("source") or "사용자 입력 비교기준", "monthly_sales": val,
                     "gap_pct": round((fin["monthly_sales"] / val - 1) * 100, 2) if val > 0 else None,
                     "warning": model["notices"]["benchmark"]}

    risks = _risks(fin, comp, growth, model)
    strategies = _strategies(comp, fin, sector, goal, model) if comp["total"] is not None else None

    sector_modules = len(comp["special_areas"])
    confidence = {
        "level": "보통" if stage["code"] != "UNDETERMINED" and sector_modules == 3 else "제한적",
        "evidence_count": len(clean), "sector_modules": sector_modules,
        "note": model["notices"]["confidence"],
    }

    return {
        "versions": {"model": model["version"], "questions": questions["version"], "industries": industries["version"]},
        "store": {"name": store.get("name") or "미입력 점포", "sector_group": sector,
                  "sector_name": model["sector_groups"][sector]["name"],
                  **{k: store.get(k) for k in ("major", "biz_model", "sub_industry", "sales_mode")},
                  "goal": goal, "goal_name": model["goals"]["items"][goal]["name"]},
        "dna": dna,
        "competence": comp,
        "finance": fin,
        "sales_growth_pct": growth,
        "risks": risks,
        "strategies": strategies,
        "stage": stage,
        "observations": clean,
        "benchmark": benchmark,
        "confidence": confidence,
        "notices": {k: model["notices"][k] for k in ("model", "residual")},
    }
