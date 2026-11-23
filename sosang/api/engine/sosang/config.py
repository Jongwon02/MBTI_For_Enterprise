"""버전이 붙은 진단모형·문항·업종분류 설정을 읽는다. 값은 코드가 아니라 config/*.json에 둔다."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

CONFIG_DIR = Path(__file__).parent / "config"


@lru_cache(maxsize=None)
def _load(name: str) -> dict[str, Any]:
    return json.loads((CONFIG_DIR / f"{name}.json").read_text(encoding="utf-8"))


def load_model(name: str = "model_v1") -> dict[str, Any]:
    return _load(name)


def load_questions(name: str = "questions_v1") -> dict[str, Any]:
    return _load(name)


def load_industries(name: str = "industries_v1") -> dict[str, Any]:
    return _load(name)
