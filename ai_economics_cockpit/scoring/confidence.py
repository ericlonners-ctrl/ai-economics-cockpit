from __future__ import annotations

CONFIDENCE_WEIGHTS = {"A": 1.0, "B": 0.85, "C": 0.65, "D": 0.35}


def confidence_weight(grade: str) -> float:
    return CONFIDENCE_WEIGHTS.get(str(grade).upper(), 0.0)

