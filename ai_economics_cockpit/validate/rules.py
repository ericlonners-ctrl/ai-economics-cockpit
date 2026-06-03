from __future__ import annotations

import pandas as pd


def validate_metric_rows(df: pd.DataFrame) -> list[str]:
    warnings: list[str] = []
    if df.empty:
        return ["No metric observations available."]
    missing_source = df["source_id"].isna() | (df["source_id"].astype(str).str.strip() == "")
    if missing_source.any():
        warnings.append("Metric observations without source_id were rejected or need correction.")
    missing_conf = df["confidence_grade"].isna() | (df["confidence_grade"].astype(str).str.strip() == "")
    if missing_conf.any():
        warnings.append("Metric observations without confidence_grade were rejected or need correction.")
    estimates = df.get("is_estimate", pd.Series(False, index=df.index)).fillna(False).astype(bool)
    missing_method = df.get("estimate_method", pd.Series("", index=df.index)).fillna("").astype(str).str.strip() == ""
    if (estimates & missing_method).any():
        warnings.append("Estimated values without estimate_method were rejected or need correction.")
    non_gaap = df["metric_id"].astype(str).str.contains("non_gaap")
    missing_label = df["notes"].fillna("").astype(str).str.lower().str.contains("non-gaap|non gaap")
    if (non_gaap & ~missing_label).any():
        warnings.append("Non-GAAP metrics must be explicitly labelled in notes.")
    private_financials = df["metric_id"].astype(str).str.contains("model_lab|cash_burn|compute_cost")
    high_conf_private = private_financials & df["confidence_grade"].isin(["A", "B"]) & df["notes"].fillna("").str.lower().str.contains("reported|leaked|estimate")
    if high_conf_private.any():
        warnings.append("Reported/leaked private-company financials should normally be confidence C unless official.")
    return warnings

