from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd

from ..config import MANUAL_DIR, load_metric_catalog
from ..validate.schemas import validate_manual_csv

MANUAL_FILES = [
    "model_lab_financials.csv",
    "enterprise_roi_observations.csv",
    "ai_budget_events.csv",
    "gpu_resale_prices.csv",
    "gpu_rental_rates.csv",
    "private_valuations.csv",
    "capex_estimates.csv",
]

REQUIRED_COLUMNS = [
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
    "is_estimate",
    "estimate_method",
    "thesis_impact",
    "severity",
    "notes",
]


def ensure_manual_templates() -> None:
    MANUAL_DIR.mkdir(parents=True, exist_ok=True)
    samples = sample_rows()
    for name in MANUAL_FILES:
        path = MANUAL_DIR / name
        if path.exists():
            continue
        rows = samples.get(name, [])
        pd.DataFrame(rows, columns=REQUIRED_COLUMNS).to_csv(path, index=False)


def sample_rows() -> dict[str, list[dict[str, Any]]]:
    return {
        "enterprise_roi_observations.csv": [
            row("2026-05-15", "Enterprise sample", "measured_roi_coverage", 32, "%", "manual_enterprise_roi", "C", "Survey-style sample observation; replace with source-backed data."),
            row("2026-05-15", "Enterprise sample", "measured_ebit_impact_coverage", 12, "%", "manual_enterprise_roi", "C", "Sample measured EBIT impact coverage."),
            row("2026-05-15", "Enterprise sample", "ai_spend_vs_budget", 125, "%", "manual_enterprise_roi", "C", "Sample budget overrun proxy."),
            row("2026-05-15", "Enterprise sample", "cost_per_accepted_output", 15, "USD", "manual_enterprise_roi", "C", "Sample accepted-output cost."),
        ],
        "ai_budget_events.csv": [
            event("2026-05-20", "Enterprise sample", "enterprise_roi", "usage_cap", "Sample AI usage caps after budget pressure", "Manual placeholder event for budget-shock monitoring.", "validates", 3, "manual_ai_budget_events", "C"),
        ],
        "model_lab_financials.csv": [
            row("2026-05-10", "Model lab sample", "model_lab_gross_margin", 28, "%", "manual_model_lab_financials", "C", "Reported/private estimate sample; not official."),
            row("2026-05-10", "Model lab sample", "cash_burn_to_revenue", 85, "%", "manual_model_lab_financials", "C", "Reported/private estimate sample; not official.", True, "manual reported estimate"),
            row("2026-05-10", "Model lab sample", "model_lab_gaap_operating_margin", -45, "%", "manual_model_lab_financials", "C", "Reported/private estimate sample; not official.", True, "manual reported estimate"),
        ],
        "gpu_resale_prices.csv": [row("2026-05-01", "GPU resale sample", "gpu_resale_price_index", 72, "index", "manual_gpu_resale_prices", "C", "Manual resale proxy sample.")],
        "gpu_rental_rates.csv": [row("2026-05-01", "GPU rental sample", "gpu_rental_rate_index", 78, "index", "manual_gpu_rental_rates", "C", "Manual rental proxy sample.")],
        "private_valuations.csv": [
            row("2026-05-01", "Private AI sample", "private_valuation_to_revenue", 35, "x", "manual_private_valuations", "C", "Manual valuation multiple sample."),
            row("2026-05-01", "Private AI sample", "external_financing_dependence", 65, "index", "manual_private_valuations", "C", "Manual financing dependence sample."),
            row("2026-05-01", "Private AI sample", "ipo_readiness_score", 45, "score", "manual_private_valuations", "C", "Manual IPO readiness sample."),
        ],
        "capex_estimates.csv": [
            row("2026-03-31", "Hyperscaler sample", "capex_to_operating_cash_flow", 52, "%", "manual_capex_estimates", "C", "Manual capex estimate sample.", True, "manual estimate"),
            row("2026-03-31", "Hyperscaler sample", "incremental_ai_revenue_to_cumulative_ai_capex", 7, "%", "manual_capex_estimates", "C", "Manual capex productivity estimate sample.", True, "manual estimate"),
            row("2026-03-31", "Hyperscaler sample", "incremental_ai_gross_profit_to_cumulative_ai_capex", 4, "%", "manual_capex_estimates", "C", "Manual capex productivity estimate sample.", True, "manual estimate"),
        ],
    }


def row(date: str, entity: str, metric_id: str, value: float, unit: str, source_id: str, confidence: str, notes: str, is_estimate: bool = False, estimate_method: str = "") -> dict[str, Any]:
    return {
        "date": date,
        "entity": entity,
        "metric_id": metric_id,
        "event_type": "",
        "value": value,
        "summary": "",
        "unit": unit,
        "source_url": source_id,
        "source_name": source_id,
        "confidence_grade": confidence,
        "is_estimate": is_estimate,
        "estimate_method": estimate_method,
        "thesis_impact": "",
        "severity": "",
        "notes": notes,
    }


def event(date: str, entity: str, pillar: str, event_type: str, title: str, summary: str, impact: str, severity: int, source_id: str, confidence: str) -> dict[str, Any]:
    return {
        "date": date,
        "entity": entity,
        "metric_id": f"{pillar}:{event_type}",
        "event_type": event_type,
        "value": "",
        "summary": summary,
        "unit": "",
        "source_url": source_id,
        "source_name": source_id,
        "confidence_grade": confidence,
        "is_estimate": False,
        "estimate_method": "",
        "thesis_impact": impact,
        "severity": severity,
        "notes": title,
    }


def load_manual_data() -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    ensure_manual_templates()
    metric_catalog = {m["metric_id"]: m for m in load_metric_catalog()}
    metric_rows: list[dict[str, Any]] = []
    event_rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    for file_name in MANUAL_FILES:
        path = MANUAL_DIR / file_name
        warnings.extend(validate_manual_csv(path))
        df = pd.read_csv(path).fillna("")
        for idx, rec in df.iterrows():
            event_type = str(rec.get("event_type", "")).strip()
            if event_type:
                pillar = infer_pillar(str(rec.get("metric_id", "")), metric_catalog)
                event_rows.append(
                    {
                        "event_id": f"{file_name}:{idx + 1}",
                        "event_date": rec["date"],
                        "entity": rec["entity"],
                        "pillar": pillar,
                        "event_type": event_type,
                        "title": rec.get("notes", ""),
                        "summary": rec.get("summary", ""),
                        "thesis_impact": rec.get("thesis_impact", ""),
                        "severity": int(float(rec.get("severity") or 0)),
                        "confidence_grade": rec.get("confidence_grade", ""),
                        "source_id": source_id_from_url(rec.get("source_url", "")),
                        "source_url": rec.get("source_url", ""),
                        "notes": rec.get("notes", ""),
                    }
                )
                continue
            metric_id = str(rec.get("metric_id", "")).strip()
            if not metric_id:
                continue
            meta = metric_catalog.get(metric_id)
            if not meta:
                warnings.append(f"{file_name} row {idx + 2} unknown metric_id {metric_id}")
                continue
            is_estimate = str(rec.get("is_estimate", "")).strip().lower() in {"true", "1", "yes"}
            estimate_method = str(rec.get("estimate_method", "")).strip()
            if is_estimate and not estimate_method:
                warnings.append(f"{file_name} row {idx + 2} estimate missing estimate_method")
                continue
            metric_rows.append(
                {
                    "metric_id": metric_id,
                    "metric_name": meta["metric_name"],
                    "pillar": meta["pillar"],
                    "entity": rec["entity"],
                    "observation_date": rec["date"],
                    "value": float(rec["value"]),
                    "unit": rec.get("unit") or meta["unit"],
                    "frequency": meta.get("frequency", "monthly"),
                    "source_id": source_id_from_url(rec.get("source_url", "")),
                    "confidence_grade": rec.get("confidence_grade", ""),
                    "is_estimate": is_estimate,
                    "estimate_method": estimate_method,
                    "vintage": date.today().isoformat(),
                    "notes": rec.get("notes", ""),
                }
            )
    return pd.DataFrame(metric_rows), pd.DataFrame(event_rows), warnings


def source_id_from_url(value: str) -> str:
    return value if value.startswith("manual_") else value


def infer_pillar(metric_id: str, catalog: dict[str, dict]) -> str:
    if ":" in metric_id:
        return metric_id.split(":", 1)[0]
    return catalog.get(metric_id, {}).get("pillar", "enterprise_roi")
