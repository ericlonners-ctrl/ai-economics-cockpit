from __future__ import annotations

from datetime import datetime

import pandas as pd
import requests
from bs4 import BeautifulSoup

from ..config import load_source_registry

USER_AGENT = "AIEconomicsCockpit/0.1"


def ingest_official_pricing(timeout: int = 20) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    rows: list[dict] = []
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
                "observation_id": f"{source['source_id']}:{datetime.utcnow().isoformat()}",
                "source_id": source["source_id"],
                "extracted_at": datetime.utcnow().isoformat(),
                "observation_date": datetime.utcnow().date().isoformat(),
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
        if source["source_id"] == "openai_api_pricing":
            rows.append(metric_row(source, "openai_weighted_token_price", "OpenAI weighted token price", 4.0, "USD/1M tokens"))
        elif source["source_id"] == "anthropic_pricing":
            rows.append(metric_row(source, "anthropic_weighted_token_price", "Anthropic weighted token price", 6.0, "USD/1M tokens"))
        elif source["source_id"] == "google_gemini_pricing":
            rows.append(metric_row(source, "google_weighted_token_price", "Google weighted token price", 3.0, "USD/1M tokens"))
    if rows:
        provider_index = sum(r["value"] for r in rows) / len(rows) * 25
        rows.append(
            {
                "metric_id": "provider_token_price_index",
                "metric_name": "Provider API pricing index",
                "pillar": "token_cost",
                "entity": "Provider basket",
                "observation_date": datetime.utcnow().date().isoformat(),
                "value": provider_index,
                "unit": "index",
                "frequency": "weekly",
                "source_id": "openai_api_pricing",
                "confidence_grade": "A",
                "is_estimate": True,
                "estimate_method": "MVP basket proxy from fetched official pricing pages",
                "vintage": datetime.utcnow().date().isoformat(),
                "notes": "Temporary deterministic MVP pricing proxy; replace with parsed model-level prices.",
            }
        )
    return pd.DataFrame(rows), pd.DataFrame(raw_rows), warnings


def metric_row(source: dict, metric_id: str, metric_name: str, value: float, unit: str) -> dict:
    return {
        "metric_id": metric_id,
        "metric_name": metric_name,
        "pillar": "token_cost",
        "entity": source["entity"],
        "observation_date": datetime.utcnow().date().isoformat(),
        "value": value,
        "unit": unit,
        "frequency": "weekly",
        "source_id": source["source_id"],
        "confidence_grade": source["confidence_grade"],
        "is_estimate": True,
        "estimate_method": "MVP official-pricing parser scaffold",
        "vintage": datetime.utcnow().date().isoformat(),
        "notes": "Official page fetched; placeholder parser emits deterministic proxy until model table parser is hardened.",
    }

