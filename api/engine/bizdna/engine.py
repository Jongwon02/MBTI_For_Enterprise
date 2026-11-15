"""Biz-DNA 진단엔진 (M3 진단 + M4 전략추천).

DB·HTTP에 의존하지 않는 순수 함수다. 1.0 시제품(legacy/bizdna/engine.py)의 계산을 그대로 재현하고,
PRD와 다른 점은 다음처럼 고쳤다.
- 미응답은 오류가 아니라 결측으로 기록하고, 응답한 문항만으로 점수를 낸다.
- 종합점수에 A~E 등급을 붙인다.
- 전략마다 적용된 규칙 ID를 남기고, 결과에 모형·문항 버전을 기록한다.
- 역량 응답이 하나도 없으면(기본진단) 유형·단계·위험요인만 산출한다.
"""
from __future__ import annotations

from typing import Any

from .config import load_model

STAGE_KEYS = ("product", "customer", "revenue", "cash", "operations", "expansion")


class DiagnosticError(ValueError):
    """입력 형식이 잘못됐을 때. 미응답은 오류가 아니다."""


def _score(value: Any, label: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not 1 <= value <= 5:
        raise DiagnosticError(f"{label}: 1~5 범위 숫자 필요")
    return float(value)


def _scale(values: list[float]) -> float:
    """1~5점 응답들을 0~100점으로 환산한다: Σ(x−1) / (4n) × 100."""
    return round(sum(x - 1 for x in values) / (4 * len(values)) * 100, 2)


def grade_for(total: float, model: dict[str, Any]) -> dict[str, str]:
    for g in model["competence"]["grades"]:
        if total >= g["min"]:
            return {"grade": g["grade"], "name": g["name"], "meaning": g["meaning"]}
    raise AssertionError("grades must cover 0")


def _diagnose_dna(answers: dict[str, Any], model: dict[str, Any]) -> dict[str, Any]:
    cfg = model["dna"]
    reverse = set(cfg["reverse_items"])
    axes: dict[str, Any] = {}
    code = ""
    missing: list[str] = []
    for axis in cfg["axes"]:
        values = []
        for item in axis["items"]:
            x = _score(answers.get(item), item)
            if x is None:
                missing.append(item)
                continue
            values.append(6 - x if item in reverse else x)
        if not values:
            axes[axis["name"]] = {"key": axis["key"], "score": None, "letter": None, "boundary": None,
                                 "answered": 0, "low_reliability": True}
            code += "?"
            continue
        score = _scale(values)
        letter = axis["a"] if score >= cfg["letter_cutoff"] else axis["b"]
        if score >= cfg["a_threshold"]:
            tendency = axis["a_name"]
        elif score <= cfg["b_threshold"]:
            tendency = axis["b_name"]
        else:
            tendency = "경계 성향"
        code += letter
        axes[axis["name"]] = {
            "key": axis["key"], "score": score, "letter": letter,
            "boundary": cfg["b_threshold"] < score < cfg["a_threshold"],
            "tendency": tendency, "a": axis["a"], "b": axis["b"],
            "answered": len(values), "low_reliability": len(values) < cfg["low_reliability_min_answers"],
        }
    profile = model["types"].get(code)
    return {"type": code, "name": profile["name"] if profile else None,
            "profile": profile, "axes": axes, "missing": missing,
            "complete": "?" not in code}


def _diagnose_competence(answers: dict[str, Any], model: dict[str, Any]) -> dict[str, Any] | None:
    cfg = model["competence"]
    domains: dict[str, float | None] = {}
    missing: list[str] = []
    for d in cfg["domains"]:
        values = []
        for n in range(1, cfg["items_per_domain"] + 1):
            code = f"{d}{n:02d}"
            x = _score(answers.get(code), code)
            if x is None:
                missing.append(code)
            else:
                values.append(x)
        domains[d] = _scale(values) if values else None
    answered = {d: s for d, s in domains.items() if s is not None}
    if not answered:
        return None
    weight_sum = sum(cfg["domains"][d]["weight"] for d in answered)
    # 응답 없는 영역은 제외하고 남은 가중치로 다시 나눈다(전 영역 응답 시 1.0과 동일).
    total = round(sum(s * cfg["domains"][d]["weight"] for d, s in answered.items()) / weight_sum, 2)
    total_items = len(cfg["domains"]) * cfg["items_per_domain"]
    return {"domains": domains, "names": {d: v["name"] for d, v in cfg["domains"].items()},
            "total": total, "grade": grade_for(total, model),
            "missing": missing, "missing_ratio": round(len(missing) / total_items, 3)}


def _diagnose_stage(answers: dict[str, Any], model: dict[str, Any]) -> dict[str, Any] | None:
    cfg = model["stage"]
    inputs = {k: _score(answers.get(k), f"stage.{k}") for k in STAGE_KEYS}
    missing = [k for k, v in inputs.items() if v is None]
    if missing:
        # Gate가 모든 지표를 쓰므로 하나라도 없으면 판정하지 않는다.
        return {"code": None, "missing": missing}
    index = sum(inputs[k] * w for k, w in cfg["weights"].items())
    provisional = min(5, max(1, int(index + 0.5)))
    stage = provisional
    applied = []
    for gate in cfg["gates"]:
        if stage >= gate["applies_from"] and any(inputs[k] < v for k, v in gate["require"].items()):
            stage = gate["fallback"]
            applied.append({"id": gate["id"], "reason": gate["reason"]})
    level = str(stage)
    return {"code": f"S{stage}", "level": stage, "name": cfg["names"][level], "task": cfg["tasks"][level],
            "weighted_index": round(index, 3), "provisional": f"S{provisional}",
            "gate_adjusted": stage != provisional, "gates_applied": applied,
            "inputs": inputs, "missing": []}


def _recommend(domain_scores: dict[str, float | None], stage_level: int | None,
               goals: list[str], flags: dict[str, bool], model: dict[str, Any]) -> list[dict[str, Any]]:
    cfg = model["strategy"]
    goal_map = model["goals"]
    w = cfg["weights"]
    out = []
    for code, st in cfg["library"].items():
        linked = {d: wt for d, wt in st["domains"].items() if domain_scores.get(d) is not None}
        # 연계 역량이 일부 결측이면 남은 가중치로 다시 나눈다.
        raw = sum((100 - domain_scores[d]) * wt for d, wt in linked.items())
        if len(linked) == len(st["domains"]):
            urgency = raw
        elif linked:
            urgency = raw / sum(linked.values()) * sum(st["domains"].values())
        else:
            urgency = 0.0
        matching = sum(1 for g in goals if code in goal_map[g]["strategies"])
        fit_bonus = impact_bonus = 0
        reasons: list[str] = []
        rules: list[str] = []
        blocked = False
        boosts = []
        for rule in cfg["rules"]:
            if "when_flag" in rule:
                hit = bool(flags.get(rule["when_flag"]))
            else:
                hit = stage_level is not None and stage_level <= rule["when_stage_max"]
            if not hit:
                continue
            touched = False
            if code in rule.get("defer", []):
                blocked = True
                touched = True
            if code in rule.get("boost", {}):
                boosts.append(rule["boost"][code])
                touched = True
            if code in rule.get("fit_bonus", {}):
                fit_bonus += rule["fit_bonus"][code]
            if code in rule.get("impact_bonus", {}):
                impact_bonus += rule["impact_bonus"][code]
            if touched:
                reasons.append(rule["reason"])
                rules.append(rule["id"])
        fit = min(100, cfg["fit_base"] + cfg["fit_per_goal"] * matching + fit_bonus)
        impact = min(100, cfg["impact_base"] + cfg["impact_per_goal"] * matching + impact_bonus)
        feasibility = cfg["feasibility_default"]
        for b in boosts:
            urgency = min(100, urgency + b)
        score = round(w["fit"] * fit + w["urgency"] * urgency + w["impact"] * impact + w["feasibility"] * feasibility, 2)
        out.append({
            "code": code, "name": st["name"], "score": score,
            "status": "deferred" if blocked else "recommended",
            "factors": {"fit": round(fit, 2), "urgency": round(urgency, 2), "impact": round(impact, 2), "feasibility": feasibility},
            "matched_goals": [g for g in goals if code in goal_map[g]["strategies"]],
            "reasons": reasons, "applied_rules": rules,
            "actions": st["actions"], "kpis": st["kpis"],
        })
    out.sort(key=lambda x: (x["status"] == "deferred", -x["score"], x["code"]))
    return out


def diagnose(payload: dict[str, Any], model: dict[str, Any] | None = None) -> dict[str, Any]:
    """1.0과 같은 입력 구조를 받는다.

    payload = {company, answers: {dna, competence, stage}, goals: [...], flags: {...}}
    """
    model = model or load_model()
    if not isinstance(payload, dict):
        raise DiagnosticError("입력은 객체여야 함")
    company = payload.get("company", {}) or {}
    answers = payload.get("answers", {}) or {}
    goals = payload.get("goals", []) or []
    flags = payload.get("flags", {}) or {}
    if not isinstance(goals, list) or any(g not in model["goals"] for g in goals):
        raise DiagnosticError("goals: 허용된 목표 코드 리스트 필요")
    if not isinstance(flags, dict) or any(not isinstance(v, bool) for v in flags.values()):
        raise DiagnosticError("flags: 불리언 값 필요")
    for section in ("dna", "competence", "stage"):
        if not isinstance(answers.get(section, {}) or {}, dict):
            raise DiagnosticError(f"answers.{section}: 객체 필요")

    dna = _diagnose_dna(answers.get("dna", {}) or {}, model)
    stage = _diagnose_stage(answers.get("stage", {}) or {}, model)
    competence = _diagnose_competence(answers.get("competence", {}) or {}, model)
    risk_labels = model["risks"]
    risks = [risk_labels[k] for k in risk_labels if flags.get(k)]

    strategies = None
    top = None
    if competence is not None:
        strategies = _recommend(competence["domains"], stage.get("level") if stage else None, goals, flags, model)
        top = [s for s in strategies if s["status"] == "recommended"][: model["strategy"]["top_n"]]

    return {
        "model_version": model["version"],
        "mode": "full" if competence is not None else "basic",
        "company": company,
        "dna": dna,
        "competence": competence,
        "stage": stage,
        "goals": [{"code": g, "name": model["goals"][g]["name"]} for g in goals],
        "risks": risks,
        "strategies": strategies,
        "top_recommended": top,
        "limitations": model["limitations"],
    }
