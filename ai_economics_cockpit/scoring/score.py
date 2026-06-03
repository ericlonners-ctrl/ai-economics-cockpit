from __future__ import annotations

from datetime import date

import pandas as pd

from ..config import load_metric_catalog, load_scoring_config
from .confidence import confidence_weight
from .normalize import metric_stress_score


def score_metrics(observations: pd.DataFrame, asof_date: str | None = None) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, list[dict]]:
    asof = pd.Timestamp(asof_date or date.today().isoformat()).date()
    catalog = pd.DataFrame(load_metric_catalog())
    scoring = load_scoring_config()
    pillar_weights = scoring["pillar_weights"]
    warnings: list[dict] = []

    if observations.empty:
        observations = pd.DataFrame(columns=["metric_id", "observation_date", "value", "confidence_grade", "source_id"])

    latest = latest_observations(observations)
    rows: list[dict] = []
    for metric in catalog.to_dict("records"):
        metric_id = metric["metric_id"]
        found = latest[latest["metric_id"] == metric_id]
        if found.empty:
            if metric.get("required"):
                warnings.append(warn("missing_required_metric", metric_id, metric["pillar"], "Required metric is missing."))
            continue
        for obs in found.to_dict("records"):
            obs_date = pd.Timestamp(obs["observation_date"]).date()
            age_days = (asof - obs_date).days
            stale = age_days > int(metric.get("max_stale_days", 75))
            if stale:
                warnings.append(warn("stale_metric", metric_id, metric["pillar"], f"{obs.get('entity')} metric is stale: {age_days} days old."))
            raw_score = metric_stress_score(
                float(obs["value"]),
                metric["directionality"],
                float(metric["green_threshold"]),
                float(metric["amber_threshold"]),
                float(metric["red_threshold"]),
            )
            c_weight = confidence_weight(obs["confidence_grade"])
            rows.append(
                {
                    **obs,
                    "metric_name": metric["metric_name"],
                    "pillar": metric["pillar"],
                    "directionality": metric["directionality"],
                    "green_threshold": metric["green_threshold"],
                    "amber_threshold": metric["amber_threshold"],
                    "red_threshold": metric["red_threshold"],
                    "metric_weight": float(metric["weight"]),
                    "required": bool(metric.get("required", False)),
                    "raw_score": round(raw_score, 4),
                    "confidence_weight": c_weight,
                    "confidence_adjusted_score": round(raw_score * c_weight, 4),
                    "age_days": age_days,
                    "stale": stale,
                }
            )
    metric_scores = pd.DataFrame(rows)
    pillar_scores = build_pillar_scores(metric_scores, catalog, warnings)
    stress_index = build_stress_index(pillar_scores, pillar_weights, asof)
    return metric_scores, pillar_scores, stress_index, warnings


def latest_observations(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    ordered = df.sort_values(["metric_id", "observation_date", "entity", "source_id"])
    return ordered.groupby(["metric_id", "entity"], as_index=False).tail(1).sort_values(["metric_id", "entity"]).reset_index(drop=True)


def build_pillar_scores(metric_scores: pd.DataFrame, catalog: pd.DataFrame, warnings: list[dict]) -> pd.DataFrame:
    rows: list[dict] = []
    for pillar, pillar_catalog in catalog.groupby("pillar", sort=True):
        scored = metric_scores[metric_scores["pillar"] == pillar] if not metric_scores.empty else pd.DataFrame()
        required_total = int(pillar_catalog["required"].sum())
        required_scored = int(scored[scored.get("required", False) == True]["metric_id"].nunique()) if not scored.empty else 0
        coverage = required_scored / required_total if required_total else (len(scored) / len(pillar_catalog) if len(pillar_catalog) else 0)
        if scored.empty:
            raw = adjusted = 0.0
            stale_count = 0
        else:
            weights = scored["metric_weight"].astype(float)
            raw = float((scored["raw_score"] * weights).sum() / weights.sum())
            adjusted = float((scored["confidence_adjusted_score"] * weights).sum() / weights.sum())
            stale_count = int(scored["stale"].sum())
            low_conf = scored[scored["confidence_grade"].isin(["C", "D"])]
            if not low_conf.empty and float(low_conf["metric_weight"].sum() / weights.sum()) > 0.5:
                warnings.append(warn("low_confidence_pillar_dominance", "", pillar, "C/D metrics account for more than half of available pillar weight."))
        rows.append(
            {
                "asof_date": date.today().isoformat(),
                "pillar": pillar,
                "raw_score": round(raw, 4),
                "confidence_adjusted_score": round(adjusted, 4),
                "data_coverage": round(coverage, 4),
                "stale_metric_count": stale_count,
                "notes": "",
            }
        )
    return pd.DataFrame(rows)


def build_stress_index(pillar_scores: pd.DataFrame, pillar_weights: dict, asof: date) -> pd.DataFrame:
    row = {
        "asof_date": asof.isoformat(),
        "ai_economic_stress_index": 0.0,
        "enterprise_roi_score": 0.0,
        "token_cost_score": 0.0,
        "model_lab_score": 0.0,
        "hyperscaler_capex_score": 0.0,
        "infra_financing_score": 0.0,
        "data_coverage": 0.0,
        "average_confidence": 0.0,
        "notes": "",
    }
    if pillar_scores.empty:
        return pd.DataFrame([row])
    total_weight = 0.0
    weighted = 0.0
    cov_weighted = 0.0
    conf_values = []
    for rec in pillar_scores.to_dict("records"):
        pillar = rec["pillar"]
        weight = float(pillar_weights.get(pillar, 0.0))
        score = float(rec["confidence_adjusted_score"])
        row[f"{pillar}_score"] = round(score, 4)
        weighted += score * weight
        cov_weighted += float(rec["data_coverage"]) * weight
        total_weight += weight
        conf_values.append(float(rec["confidence_adjusted_score"]) / float(rec["raw_score"]) if rec["raw_score"] else 0.0)
    row["ai_economic_stress_index"] = round(weighted / total_weight, 4) if total_weight else 0.0
    row["data_coverage"] = round(cov_weighted / total_weight, 4) if total_weight else 0.0
    row["average_confidence"] = round(sum(conf_values) / len(conf_values), 4) if conf_values else 0.0
    return pd.DataFrame([row])


def warn(kind: str, metric_id: str, pillar: str, message: str) -> dict:
    return {"type": kind, "metric_id": metric_id, "pillar": pillar, "message": message}
