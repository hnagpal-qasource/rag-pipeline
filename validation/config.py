from __future__ import annotations

import json
from pathlib import Path

DEFAULT_CONFIG = {
    "thresholds": {
        "retrieval_relevance": 0.65,
        "groundedness": 0.60,
        "faithfulness": 0.65,
        "answer_relevancy": 0.65,
        "context_precision": 0.60,
        "context_recall": 0.60,
    },
    "min_cases": 3,
    "require_ragas": True,
}


def load_config(path: str | None = None) -> dict:
    if not path:
        return DEFAULT_CONFIG

    cfg_path = Path(path)
    if not cfg_path.exists():
        raise FileNotFoundError(f"Config file not found: {cfg_path}")

    with cfg_path.open("r", encoding="utf-8") as f:
        user_cfg = json.load(f)

    merged = DEFAULT_CONFIG.copy()
    merged_thresholds = DEFAULT_CONFIG["thresholds"].copy()
    merged_thresholds.update(user_cfg.get("thresholds", {}))
    merged.update(user_cfg)
    merged["thresholds"] = merged_thresholds
    return merged
