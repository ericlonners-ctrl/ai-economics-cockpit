from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd
import requests
from bs4 import BeautifulSoup

from ..config import load_source_registry, load_token_pricing_config

USER_AGENT = "AIEconomicsCockpit/0.1"


def ingest_official_pricing(timeout: int = 20) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    rows = curated_token_price_rows()
    raw_rows: list[dict] = []
    warnings: list[str] = []
    sources = [s for s in load_source_registry() if s["source_type"] == "official_pricing" and s["active"]]
    for source in sources:
        try:
            response = requests.get(source["url"], timeout=timeout, headers={"User-Agent": USER_AGENT})
            response.raise_for_status()
        except requests.RequestException as exc:
            warnings.append(f"official pricing fetch failed for {source['source_id']}: {exc}")
            continue
        soup = BeautifulSoup(response.text, "html.parser")
        text = " ".join(soup.get_text(" ").split())
        raw_rows.append(
            {
                "observation_id": f"{source['source_id']}:{now().isoformat()}",
                "source_id": source["source_id"],
                "extracted_at": now().isoformat(),
                "observation_date": now().date().isoformat(),
                "entity": source["entity"],
                "metric_id": "provider_token_price_index",
                "raw_value": "",
                "raw_unit": "",
                "raw_text": text[:1000],
                "source_url": source["url"],
                "extraction_method": "html_text_best_effort",
                "confidence_grade": source["confidence_grade"],
                "notes": "Official pricing page fetched; metric extraction is scaffolded for manual review.",
            }
        )
    return pd.DataFrame(rows), pd.DataFrame(raw_rows), warnings


def curated_token_price_rows() -> list[dict]:
    cfg = load_token_pricing_config()
    models = cfg["models"]
    rows: list[dict] = []
    by_provider: dict[str, list[dict]] = {}
    for model in models:
        by_provider.setdefault(model["provider"], []).append(model)

    metric_map = {
        "OpenAI": ("openai_weighted_token_price", "OpenAI weighted token price"),
        "Anthropic": ("anthropic_weighted_token_price", "Anthropic weighted token price"),
        "Google": ("google_weighted_token_price", "Google weighted token price"),
    }
    for provider, provider_models in sorted(by_provider.items()):
        metric_id, metric_name = metric_map[provider]
        weighted = sum(blended_task_price(m) for m in provider_models) / len(provider_models)
        rows.append(
            metric_row(
                provider_models[0],
                provider,
                metric_id,
                metric_name,
                weighted,
                "USD/task proxy",
                True,
                "Mean blended task proxy from curated official price card: 1k input + 500 output.",
            )
        )

    all_model_prices = [blended_task_price(m) for m in models]
    provider_index = sum(all_model_prices) / len(all_model_prices) * 10.0
    output_input_ratio = sum(float(m["output_usd_per_mtok"]) / float(m["input_usd_per_mtok"]) for m in models) / len(models)
    cached_discount_index = sum(float(m["cached_input_usd_per_mtok"]) / float(m["input_usd_per_mtok"]) for m in models) / len(models) * 100.0
    long_context = 100.0

    first = models[0]
    rows.extend(
        [
            metric_row(first, "Provider basket", "provider_token_price_index", "Provider API pricing index", provider_index, "index", True, "Curated official provider price card; 1k input + 500 output blended task proxy indexed x10."),
            metric_row(first, "Provider basket", "output_to_input_price_ratio", "Output/input price ratio", output_input_ratio, "ratio", True, "Mean output/input ratio across curated official price-card models."),
            metric_row(first, "Provider basket", "cached_token_discount_index", "Cached token discount index", cached_discount_index, "index", True, "Mean cached-input discount ratio across curated official price-card models."),
            metric_row(first, "Provider basket", "long_context_cost_index", "Long-context surcharge / context-cost index", long_context, "index", True, "Set to neutral until parsed long-context model mix is complete."),
            metric_row(first, "Provider basket", "estimated_cost_per_agentic_task", "Estimated cost per task", sum(all_model_prices) / len(all_model_prices), "USD", True, "Curated official provider price card; 1k input + 500 output blended proxy."),
            metric_row(first, "Provider basket", "output_tokens_per_task", "Output tokens per task", 500.0, "tokens", True, "Default task-shape assumption for official-pricing proxy."),
            metric_row(first, "Provider basket", "tool_use_overhead_ratio", "Tool-use / agentic-overhead cost", 1.35, "ratio", True, "Conservative placeholder overhead until real task telemetry is added."),
        ]
    )
    return rows


def blended_task_price(model: dict) -> float:
    input_cost = float(model["input_usd_per_mtok"]) * 0.001
    output_cost = float(model["output_usd_per_mtok"]) * 0.0005
    return input_cost + output_cost


def metric_row(
    source: dict,
    entity: str,
    metric_id: str,
    metric_name: str,
    value: float,
    unit: str,
    is_estimate: bool,
    estimate_method: str,
) -> dict:
    return {
        "metric_id": metric_id,
        "metric_name": metric_name,
        "pillar": "token_cost",
        "entity": entity,
        "observation_date": load_token_pricing_config()["asof_date"],
        "value": value,
        "unit": unit,
        "frequency": "weekly",
        "source_id": source["source_id"],
        "confidence_grade": source["confidence_grade"],
        "is_estimate": is_estimate,
        "estimate_method": estimate_method,
        "vintage": now().date().isoformat(),
        "notes": f"{source.get('model', entity)} official price-card ingestion. {source.get('notes', '')}",
    }


def now() -> datetime:
    return datetime.now(UTC)
