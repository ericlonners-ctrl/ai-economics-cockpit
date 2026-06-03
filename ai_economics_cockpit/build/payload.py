from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from ..config import PROCESSED_DIR, load_falsification_config, load_metric_catalog, load_source_registry


def build_payload(
    metric_scores: pd.DataFrame,
    pillar_scores: pd.DataFrame,
    stress_index: pd.DataFrame,
    event_log: pd.DataFrame,
    warnings: list[dict],
    output_path: Path | None = None,
) -> dict[str, Any]:
    output_path = output_path or PROCESSED_DIR / "dashboard_payload.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    warnings = list(warnings)
    sample_count = sample_observation_count(metric_scores, event_log)
    if sample_count:
        warnings.append(
            {
                "type": "sample_data_present",
                "metric_id": "",
                "pillar": "",
                "message": f"{sample_count} sample or placeholder observations are present; replace with source-backed evidence before treating scores as decision-grade.",
            }
        )
    index = stress_index.iloc[0].to_dict()
    asof = index["asof_date"]
    indicators = evaluate_indicators(metric_scores)
    payload = {
        "asof_date": asof,
        "stress_index": index,
        "pillar_scores": records(pillar_scores),
        "metric_catalog": load_metric_catalog(),
        "latest_metrics": records(metric_scores.sort_values(["pillar", "metric_id"])) if not metric_scores.empty else [],
        "time_series": build_time_series(metric_scores),
        "event_log": records(event_log.sort_values("event_date", ascending=False)) if not event_log.empty else [],
        "source_registry": load_source_registry(),
        "warnings": sorted(warnings, key=lambda x: (x.get("type", ""), x.get("pillar", ""), x.get("metric_id", ""))),
        "data_quality": {
            "metric_count": int(len(metric_scores)),
            "event_count": int(len(event_log)),
            "data_coverage": index.get("data_coverage", 0),
            "average_confidence": index.get("average_confidence", 0),
            "low_confidence_metric_count": int(metric_scores["confidence_grade"].isin(["C", "D"]).sum()) if not metric_scores.empty else 0,
            "sample_observation_count": sample_count,
        },
        "falsification_indicators": indicators["falsification_indicators"],
        "validation_indicators": indicators["validation_indicators"],
    }
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")
    return payload


def records(df: pd.DataFrame) -> list[dict[str, Any]]:
    return json.loads(df.to_json(orient="records", date_format="iso"))


def build_time_series(metric_scores: pd.DataFrame) -> dict[str, list[dict[str, Any]]]:
    if metric_scores.empty:
        return {}
    out: dict[str, list[dict[str, Any]]] = {}
    for metric_id, df in metric_scores.groupby("metric_id"):
        out[metric_id] = records(df.sort_values("observation_date")[["observation_date", "value", "raw_score", "confidence_adjusted_score"]])
    return out


def sample_observation_count(metric_scores: pd.DataFrame, event_log: pd.DataFrame) -> int:
    count = 0
    if not metric_scores.empty:
        text = (
            metric_scores.get("notes", pd.Series("", index=metric_scores.index)).fillna("").astype(str)
            + " "
            + metric_scores.get("entity", pd.Series("", index=metric_scores.index)).fillna("").astype(str)
        ).str.lower()
        count += int(text.str.contains("sample|placeholder").sum())
    if not event_log.empty:
        text = (
            event_log.get("notes", pd.Series("", index=event_log.index)).fillna("").astype(str)
            + " "
            + event_log.get("summary", pd.Series("", index=event_log.index)).fillna("").astype(str)
        ).str.lower()
        count += int(text.str.contains("sample|placeholder").sum())
    return count


def evaluate_indicators(metric_scores: pd.DataFrame) -> dict[str, list[dict]]:
    cfg = load_falsification_config()
    latest = {r["metric_id"]: r for r in metric_scores.to_dict("records")} if not metric_scores.empty else {}
    result: dict[str, list[dict]] = {"falsification_indicators": [], "validation_indicators": []}
    for key in result:
        for ind in cfg.get(key, []):
            row = latest.get(ind["metric_id"])
            value = None if row is None else float(row["value"])
            triggered = False
            if value is not None and ind["condition"] == "above":
                triggered = value > float(ind["threshold"])
            if value is not None and ind["condition"] == "below":
                triggered = value < float(ind["threshold"])
            result[key].append({**ind, "latest_value": value, "triggered": triggered})
    return result
