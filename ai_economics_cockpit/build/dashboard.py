from __future__ import annotations

from pathlib import Path

from ..config import ARTIFACTS_DIR, DASHBOARD_DIR


def write_dashboard_assets() -> None:
    DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)
    (DASHBOARD_DIR / "assets").mkdir(parents=True, exist_ok=True)
    # Assets are source-controlled; this hook exists for future generated assets.


def write_build_report(commands: list[str], test_result: str, warnings: list[dict]) -> Path:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    path = ARTIFACTS_DIR / "latest_dashboard_build_report.md"
    warning_lines = "\n".join(f"- {w.get('type')}: {w.get('pillar')} {w.get('metric_id')} - {w.get('message')}" for w in warnings) or "- None"
    body = f"""# AI Economics Cockpit Build Report

## Files Created

- data/ai_economics.duckdb
- data/processed/latest_metric_snapshot.parquet
- data/processed/latest_scores.parquet
- data/processed/dashboard_payload.json
- dashboard/index.html

## Commands Run

{chr(10).join(f"- `{c}`" for c in commands)}

## Test Results

{test_result}

## Source Coverage

Manual sample data is ingested for enterprise ROI, model-lab financials, hyperscaler capex estimates, GPU resale/rental proxies, private valuations, and event evidence. Official pricing ingestion is scaffolded and emits warnings rather than failing when pages are unavailable.

## Missing Data / Warnings

{warning_lines}

## Recommended Next Data Additions

- Replace sample enterprise ROI observations with named survey or company budget data.
- Add parsed model-level official pricing tables for OpenAI, Anthropic, Google, Azure, and Bedrock.
- Add company filing-derived hyperscaler capex and depreciation observations.
- Add source-backed GPU resale/rental series.
- Add private-company financial observations only with explicit confidence grades and estimate methods.
"""
    path.write_text(body, encoding="utf-8")
    return path

