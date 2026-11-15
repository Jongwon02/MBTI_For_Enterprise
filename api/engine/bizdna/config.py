"""버전이 붙은 진단모형·문항 설정을 읽는다. 값은 코드가 아니라 config/*.json에 둔다."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

CONFIG_DIR = Path(__file__).parent / "config"
DEFAULT_MODEL = "model_v1"
DEFAULT_QUESTIONS = "questions_v1"


@lru_cache(maxsize=None)
def load_model(name: str = DEFAULT_MODEL) -> dict[str, Any]:
    return json.loads((CONFIG_DIR / f"{name}.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=None)
def load_questions(name: str = DEFAULT_QUESTIONS) -> dict[str, Any]:
    return json.loads((CONFIG_DIR / f"{name}.json").read_text(encoding="utf-8"))
