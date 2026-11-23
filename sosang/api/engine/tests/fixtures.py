"""legacy/mvp_v4 입력 JSON을 이 엔진의 입력 형식으로 바꾼다 (기준 사례 재현용)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "v4"

AREA_CODES = {"상권·입지": "A", "상품·서비스": "B", "고객관리": "C", "마케팅·판로": "D",
              "재무·수익": "E", "점포운영": "F", "디지털": "G", "경영자·미래대응": "H"}
AXIS_ITEMS = {"G/S": 1, "D/E": 5, "N/R": 9, "P/O": 13}
SECTORS = {"외식업": "food", "도소매업": "retail", "생활서비스업": "life", "기타": "other"}
PREFIX = {"food": "FOOD", "retail": "RETAIL", "life": "LIFE"}
GOALS = {"수익성 개선": "profit", "매출확대": "sales", "단골확보": "regulars", "운영효율": "efficiency", "사업전환": "pivot"}


def load_v4(name: str) -> dict[str, Any]:
    return json.loads((FIXTURE_DIR / f"{name}.json").read_text(encoding="utf-8"))


def from_v4(v4: dict[str, Any]) -> dict[str, Any]:
    p = v4["profile"]
    sector = SECTORS.get(p.get("sector", "기타"), "other")
    dna = {}
    for axis, start in AXIS_ITEMS.items():
        for i, v in enumerate(v4["dna"][axis]):
            dna[f"D{start + i:02d}"] = v
    competence = {f"{AREA_CODES[a]}{i + 1:02d}": v for a, vs in v4["responses"].items() for i, v in enumerate(vs)}
    special = {}
    for a, vs in (v4.get("sector_answers") or {}).items():
        for i, v in enumerate(vs):
            special[f"{PREFIX[sector]}-{AREA_CODES[a]}{i + 1:02d}"] = v
    store = {"name": p.get("name"), "sector_group": sector}
    if p.get("target"):
        store["goal"] = GOALS[p["target"]]
    payload = {
        "store": store,
        # v4는 총비용(임대료 포함) 한 칸이었다: 총비용 − 임대료를 기타비용에 넣는다 (CLAUDE.md 4.9)
        "finance": {"monthly_sales": p["monthly_sales"], "rent": p["monthly_rent"],
                    "other_cost": p["monthly_cost"] - p["monthly_rent"]},
        "answers": {"dna": dna, "competence": competence, "special": special},
    }
    if v4.get("observations"):
        payload["observations"] = v4["observations"]
    if v4.get("benchmark"):
        payload["benchmark"] = v4["benchmark"]
    return payload


def case(name: str) -> dict[str, Any]:
    return from_v4(load_v4(name))
