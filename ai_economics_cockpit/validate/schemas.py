from __future__ import annotations

from pathlib import Path

import pandas as pd

SOURCE_REQUIRED = {"source_id", "source_name", "source_type", "confidence_grade", "refresh_frequency", "active"}
METRIC_REQUIRED = {
    "metric_id",
    "metric_name",
    "pillar",
    "directionality",
    "green_threshold",
    "amber_threshold",
    "red_threshold",
    "unit",
    "weight",
}
MANUAL_REQUIRED = {
    "date",
    "entity",
    "metric_id",
    "event_type",
    "value",
    "summary",
    "unit",
    "source_url",
    "source_name",
    "confidence_grade",
    "notes",
}
EVENT_REQUIRED = {"event_type", "summary", "severity", "thesis_impact"}
VALID_CONFIDENCE = {"A", "B", "C", "D"}


def validate_source_registry(sources: list[dict]) -> list[str]:
    warnings: list[str] = []
    for source in sources:
        missing = SOURCE_REQUIRED - set(source)
        if missing:
            warnings.append(f"source {source.get('source_id', '<missing>')} missing {sorted(missing)}")
        if source.get("confidence_grade") not in VALID_CONFIDENCE:
            warnings.append(f"source {source.get('source_id')} has invalid confidence grade")
    return warnings


def validate_metric_catalog(metrics: list[dict]) -> list[str]:
    warnings: list[str] = []
    seen: set[str] = set()
    for metric in metrics:
        missing = METRIC_REQUIRED - set(metric)
        if missing:
            warnings.append(f"metric {metric.get('metric_id', '<missing>')} missing {sorted(missing)}")
        if metric.get("metric_id") in seen:
            warnings.append(f"duplicate metric_id {metric.get('metric_id')}")
        seen.add(metric.get("metric_id", ""))
        if metric.get("directionality") not in {"higher_validates_thesis", "lower_validates_thesis"}:
            warnings.append(f"metric {metric.get('metric_id')} has invalid directionality")
    return warnings


def validate_manual_csv(path: Path) -> list[str]:
    df = pd.read_csv(path)
    missing = MANUAL_REQUIRED - set(df.columns)
    warnings = [f"{path.name} missing {sorted(missing)}"] if missing else []
    if "confidence_grade" in df:
        bad = sorted(set(df["confidence_grade"].dropna()) - VALID_CONFIDENCE)
        if bad:
            warnings.append(f"{path.name} invalid confidence grades {bad}")
    event_rows = df[df.get("event_type", pd.Series(dtype=str)).fillna("").astype(str).str.len() > 0]
    for idx, row in event_rows.iterrows():
        for col in EVENT_REQUIRED:
            if pd.isna(row.get(col)) or str(row.get(col)).strip() == "":
                warnings.append(f"{path.name} row {idx + 2} event missing {col}")
    return warnings

