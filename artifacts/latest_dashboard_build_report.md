# AI Economics Cockpit Build Report

## Files Created

- data/ai_economics.duckdb
- data/processed/latest_metric_snapshot.parquet
- data/processed/latest_scores.parquet
- data/processed/dashboard_payload.json
- dashboard/index.html

## Commands Run

- `python -m ai_economics_cockpit init`
- `python -m ai_economics_cockpit ingest --manual --sources official_pricing,sec_filings`
- `python -m ai_economics_cockpit build`
- `python -m ai_economics_cockpit validate`

## Test Results

Validation passed. The GitHub Pages workflow runs `pytest` after this build step; locally run `.venv/bin/pytest` for the full suite.

## Source Coverage

Manual sample data is ingested for enterprise ROI, model-lab financials, hyperscaler capex estimates, GPU resale/rental proxies, private valuations, and event evidence. Official pricing ingestion is scaffolded and emits warnings rather than failing when pages are unavailable.

## Missing Data / Warnings

- missing_required_metric: enterprise_roi ai_spend_to_it_budget - Required metric is missing.
- stale_metric: hyperscaler_capex capex - Oracle metric is stale: 276 days old.
- stale_metric: hyperscaler_capex capex_to_operating_cash_flow - Oracle metric is stale: 276 days old.
- stale_metric: hyperscaler_capex capex_to_revenue - Oracle metric is stale: 276 days old.
- low_confidence_pillar_dominance: enterprise_roi  - C/D metrics account for more than half of available pillar weight.
- low_confidence_pillar_dominance: infra_financing  - C/D metrics account for more than half of available pillar weight.
- low_confidence_pillar_dominance: model_lab  - C/D metrics account for more than half of available pillar weight.

## Recommended Next Data Additions

- Replace sample enterprise ROI observations with named survey or company budget data.
- Add parsed model-level official pricing tables for OpenAI, Anthropic, Google, Azure, and Bedrock.
- Add company filing-derived hyperscaler capex and depreciation observations.
- Add source-backed GPU resale/rental series.
- Add private-company financial observations only with explicit confidence grades and estimate methods.
