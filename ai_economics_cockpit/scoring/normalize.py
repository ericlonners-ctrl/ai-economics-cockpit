from __future__ import annotations


def metric_stress_score(value: float, directionality: str, green: float, amber: float, red: float) -> float:
    """Map a metric value to a 0-100 stress score using green/amber/red thresholds."""
    if directionality == "higher_validates_thesis":
        if value <= green:
            return 0.0
        if value >= red:
            return 100.0
        if value <= amber:
            return 50.0 * (value - green) / (amber - green)
        return 50.0 + 50.0 * (value - amber) / (red - amber)

    if directionality == "lower_validates_thesis":
        if value >= green:
            return 0.0
        if value <= red:
            return 100.0
        if value >= amber:
            return 50.0 * (green - value) / (green - amber)
        return 50.0 + 50.0 * (amber - value) / (amber - red)

    raise ValueError(f"Unsupported directionality: {directionality}")

