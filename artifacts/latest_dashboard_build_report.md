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

Validation passed. The GitHub Pages workflow runs `pytest` before the online publish build; locally run `.venv/bin/pytest` for the full suite.

## Source Coverage

Manual sample data is ingested for enterprise ROI, model-lab financials, hyperscaler capex estimates, GPU resale/rental proxies, private valuations, and event evidence. Official pricing ingestion is scaffolded and emits warnings rather than failing when pages are unavailable.

## Missing Data / Warnings

- missing_required_metric: enterprise_roi ai_spend_to_it_budget - Required metric is missing.
- stale_metric: enterprise_roi ai_spend_vs_budget - Enterprise sample metric is stale: 148 days old.
- stale_metric: enterprise_roi measured_roi_coverage - Enterprise sample metric is stale: 148 days old.
- stale_metric: enterprise_roi measured_ebit_impact_coverage - Enterprise sample metric is stale: 148 days old.
- stale_metric: enterprise_roi cost_per_accepted_output - Enterprise sample metric is stale: 148 days old.
- stale_metric: token_cost openai_weighted_token_price - OpenAI metric is stale: 129 days old.
- stale_metric: token_cost anthropic_weighted_token_price - Anthropic metric is stale: 129 days old.
- stale_metric: token_cost google_weighted_token_price - Google metric is stale: 129 days old.
- stale_metric: token_cost provider_token_price_index - Provider basket metric is stale: 129 days old.
- stale_metric: token_cost output_to_input_price_ratio - Provider basket metric is stale: 129 days old.
- stale_metric: token_cost cached_token_discount_index - Provider basket metric is stale: 129 days old.
- stale_metric: token_cost long_context_cost_index - Provider basket metric is stale: 129 days old.
- stale_metric: token_cost estimated_cost_per_agentic_task - Provider basket metric is stale: 129 days old.
- stale_metric: token_cost output_tokens_per_task - Provider basket metric is stale: 129 days old.
- stale_metric: token_cost tool_use_overhead_ratio - Provider basket metric is stale: 129 days old.
- stale_metric: model_lab model_lab_gross_margin - Model lab sample metric is stale: 153 days old.
- stale_metric: model_lab model_lab_gaap_operating_margin - Model lab sample metric is stale: 153 days old.
- stale_metric: model_lab cash_burn_to_revenue - Model lab sample metric is stale: 153 days old.
- stale_metric: hyperscaler_capex capex - AMD metric is stale: 196 days old.
- stale_metric: hyperscaler_capex capex - Alphabet metric is stale: 193 days old.
- stale_metric: hyperscaler_capex capex - Broadcom metric is stale: 251 days old.
- stale_metric: hyperscaler_capex capex - Meta metric is stale: 193 days old.
- stale_metric: hyperscaler_capex capex - NVIDIA metric is stale: 167 days old.
- stale_metric: hyperscaler_capex capex_to_operating_cash_flow - AMD metric is stale: 196 days old.
- stale_metric: hyperscaler_capex capex_to_operating_cash_flow - Alphabet metric is stale: 193 days old.
- stale_metric: hyperscaler_capex capex_to_operating_cash_flow - Broadcom metric is stale: 251 days old.
- stale_metric: hyperscaler_capex capex_to_operating_cash_flow - Hyperscaler sample metric is stale: 193 days old.
- stale_metric: hyperscaler_capex capex_to_operating_cash_flow - Meta metric is stale: 193 days old.
- stale_metric: hyperscaler_capex capex_to_operating_cash_flow - NVIDIA metric is stale: 167 days old.
- stale_metric: hyperscaler_capex capex_to_revenue - AMD metric is stale: 196 days old.
- stale_metric: hyperscaler_capex capex_to_revenue - Broadcom metric is stale: 251 days old.
- stale_metric: hyperscaler_capex capex_to_revenue - Meta metric is stale: 193 days old.
- stale_metric: hyperscaler_capex incremental_ai_revenue_to_cumulative_ai_capex - Hyperscaler sample metric is stale: 193 days old.
- stale_metric: hyperscaler_capex incremental_ai_gross_profit_to_cumulative_ai_capex - Hyperscaler sample metric is stale: 193 days old.
- stale_metric: infra_financing gpu_resale_price_index - GPU resale sample metric is stale: 162 days old.
- stale_metric: infra_financing gpu_rental_rate_index - GPU rental sample metric is stale: 162 days old.
- stale_metric: infra_financing private_valuation_to_revenue - Private AI sample metric is stale: 162 days old.
- stale_metric: infra_financing external_financing_dependence - Private AI sample metric is stale: 162 days old.
- stale_metric: infra_financing ipo_readiness_score - Private AI sample metric is stale: 162 days old.
- low_confidence_pillar_dominance: enterprise_roi  - C/D metrics account for more than half of available pillar weight.
- low_confidence_pillar_dominance: infra_financing  - C/D metrics account for more than half of available pillar weight.
- low_confidence_pillar_dominance: model_lab  - C/D metrics account for more than half of available pillar weight.

## Recommended Next Data Additions

- Replace sample enterprise ROI observations with named survey or company budget data.
- Add parsed model-level official pricing tables for OpenAI, Anthropic, Google, Azure, and Bedrock.
- Add company filing-derived hyperscaler capex and depreciation observations.
- Add source-backed GPU resale/rental series.
- Add private-company financial observations only with explicit confidence grades and estimate methods.
