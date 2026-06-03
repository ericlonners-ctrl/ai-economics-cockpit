# AI Economics Cockpit

Deterministic local cockpit for monitoring whether the bearish AI-economics thesis is being validated or falsified by quantitative evidence.

The cockpit tracks the AI Economic Stress Index, a 0-100 composite where higher values indicate stronger evidence of economic stress from weak ROI, hidden token costs, model-lab cash burn, hyperscaler capex overbuild, and infrastructure or exit-liquidity risk.

## Thesis Monitored

The monitored thesis is that generative AI adoption may be economically fragile once true token, inference, training, depreciation, power, supervision, and financing costs are measured. The cockpit is designed to show both validating and falsifying evidence, with missing data and low-confidence observations visible rather than hidden.

## Pillars

- Enterprise ROI and budget shock: 25%
- Token economics and subsidy withdrawal: 20%
- Model-lab profitability and cash burn: 20%
- Hyperscaler capex productivity: 20%
- Infrastructure residual value, financing, and IPO risk: 15%

## Scoring

Metric thresholds live in `config/metric_catalog.yaml`; pillar and confidence weights live in `config/scoring.yaml`.

Each metric is converted to a 0-100 stress score. Higher score means more validation of the bearish thesis. Pillar scores are weighted averages of available metric scores. The AI Economic Stress Index is the weighted average of pillar scores.

Confidence-adjusted score = raw score * confidence weight:

- A: 1.00
- B: 0.85
- C: 0.65
- D: 0.35

Missing required metrics reduce coverage and create warnings. Stale metrics are flagged and are not silently treated as fresh.

## Install

```bash
cd /Users/liberel/code/ai-economics-cockpit
python3 -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
```

## Commands

```bash
python -m ai_economics_cockpit init
python -m ai_economics_cockpit ingest --manual
python -m ai_economics_cockpit ingest --sources official_pricing
python -m ai_economics_cockpit build
python -m ai_economics_cockpit validate
python -m ai_economics_cockpit serve
python -m ai_economics_cockpit all
```

The dashboard is at `dashboard/index.html` and loads `../data/processed/dashboard_payload.json`.

## Manual Evidence

Manual CSV templates live in `data/manual/`. Every row must include source URL, source name, confidence grade, and notes. Estimates must set `is_estimate=true` and include `estimate_method`.

Event evidence belongs in `data/manual/ai_budget_events.csv`. Non-hard-data observations should be represented as event-log rows with severity, thesis impact, source, and confidence.

## Adding Metrics

Add the metric to `config/metric_catalog.yaml`, including pillar, thresholds, directionality, weight, stale-day rule, and data-quality rule. Then add observations through a manual CSV or importer.

## Refresh

Run:

```bash
python -m ai_economics_cockpit all
```

This creates:

- `data/ai_economics.duckdb`
- `data/processed/latest_metric_snapshot.parquet`
- `data/processed/latest_scores.parquet`
- `data/processed/dashboard_payload.json`
- `artifacts/latest_dashboard_build_report.md`

## Limitations

Many model-lab and private-market metrics are manual or reported estimates. C/D evidence is visible and confidence-adjusted. The cockpit monitors a thesis; it does not prove it.
