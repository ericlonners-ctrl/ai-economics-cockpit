from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pandas as pd
import requests

from ..config import load_sec_companies_config

SEC_COMPANYFACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
USER_AGENT = "AIEconomicsCockpit/0.1 ericlonners-ctrl"

FACT_TAGS = {
    "capex": [
        "PaymentsToAcquireProductiveAssets",
        "PaymentsToAcquirePropertyPlantAndEquipment",
        "PaymentsForProceedsFromProductiveAssets",
        "PropertyPlantAndEquipmentAdditions",
    ],
    "operating_cash_flow": ["NetCashProvidedByUsedInOperatingActivities"],
    "revenue": ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax"],
}


def ingest_sec_companyfacts(timeout: int = 20) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    rows: list[dict[str, Any]] = []
    raw_rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    for company in load_sec_companies_config()["companies"]:
        try:
            response = requests.get(
                SEC_COMPANYFACTS_URL.format(cik=company["cik"]),
                timeout=timeout,
                headers={"User-Agent": USER_AGENT},
            )
            response.raise_for_status()
            facts = response.json()
        except requests.RequestException as exc:
            warnings.append(f"SEC companyfacts fetch failed for {company['entity']}: {exc}")
            continue

        raw_rows.append(raw_observation(company, facts))
        extracted = {
            name: latest_usd_fact(facts, tags)
            for name, tags in FACT_TAGS.items()
        }
        if not extracted["capex"]:
            warnings.append(f"SEC capex fact missing for {company['entity']}")
            continue

        capex = abs(float(extracted["capex"]["val"]))
        obs_date = extracted["capex"]["end"]
        rows.append(metric_row(company, "capex", "Total capex", capex / 1_000_000, "USD mn", obs_date, "SEC companyfacts capital expenditure fact."))

        ocf = extracted.get("operating_cash_flow")
        if ocf and float(ocf["val"]) != 0:
            rows.append(
                metric_row(
                    company,
                    "capex_to_operating_cash_flow",
                    "Capex / operating cash flow",
                    capex / abs(float(ocf["val"])) * 100.0,
                    "%",
                    max(obs_date, ocf["end"]),
                    "SEC companyfacts capex divided by operating cash flow.",
                )
            )
        else:
            warnings.append(f"SEC operating cash flow fact missing for {company['entity']}")

        revenue = extracted.get("revenue")
        if revenue and float(revenue["val"]) != 0:
            rows.append(
                metric_row(
                    company,
                    "capex_to_revenue",
                    "Capex / revenue",
                    capex / abs(float(revenue["val"])) * 100.0,
                    "%",
                    max(obs_date, revenue["end"]),
                    "SEC companyfacts capex divided by revenue.",
                )
            )
        else:
            warnings.append(f"SEC revenue fact missing for {company['entity']}")

    return pd.DataFrame(rows), pd.DataFrame(raw_rows), warnings


def latest_usd_fact(facts: dict[str, Any], tags: list[str]) -> dict[str, Any] | None:
    us_gaap = facts.get("facts", {}).get("us-gaap", {})
    candidates: list[dict[str, Any]] = []
    for tag in tags:
        units = us_gaap.get(tag, {}).get("units", {})
        for unit_name in ["USD"]:
            for item in units.get(unit_name, []):
                if item.get("form") not in {"10-K", "10-Q"}:
                    continue
                if item.get("fp") not in {"FY", "Q1", "Q2", "Q3"}:
                    continue
                if "val" not in item or "end" not in item:
                    continue
                duration = period_days(item)
                if item.get("fp") in {"Q1", "Q2", "Q3"} and duration is not None and duration > 120:
                    continue
                if item.get("fp") == "FY" and duration is not None and duration > 390:
                    continue
                candidates.append({**item, "tag": tag, "duration_days": duration or 9999})
        if candidates:
            break
    if not candidates:
        return None
    return sorted(candidates, key=lambda r: (r.get("end", ""), r.get("filed", ""), -int(r.get("duration_days", 9999))))[-1]


def period_days(item: dict[str, Any]) -> int | None:
    if not item.get("start") or not item.get("end"):
        return None
    try:
        return (datetime.fromisoformat(item["end"]) - datetime.fromisoformat(item["start"])).days
    except ValueError:
        return None


def metric_row(company: dict, metric_id: str, metric_name: str, value: float, unit: str, observation_date: str, notes: str) -> dict:
    return {
        "metric_id": metric_id,
        "metric_name": metric_name,
        "pillar": "hyperscaler_capex",
        "entity": company["entity"],
        "observation_date": observation_date,
        "value": value,
        "unit": unit,
        "frequency": "quarterly",
        "source_id": company["source_id"],
        "confidence_grade": "A",
        "is_estimate": False,
        "estimate_method": "",
        "vintage": datetime.now(UTC).date().isoformat(),
        "notes": notes,
    }


def raw_observation(company: dict, facts: dict[str, Any]) -> dict:
    return {
        "observation_id": f"sec_companyfacts:{company['cik']}:{datetime.now(UTC).isoformat()}",
        "source_id": company["source_id"],
        "extracted_at": datetime.now(UTC).isoformat(),
        "observation_date": datetime.now(UTC).date().isoformat(),
        "entity": company["entity"],
        "metric_id": "sec_companyfacts",
        "raw_value": "",
        "raw_unit": "json",
        "raw_text": f"SEC companyfacts keys: {', '.join(sorted(facts.get('facts', {}).get('us-gaap', {}).keys())[:25])}",
        "source_url": SEC_COMPANYFACTS_URL.format(cik=company["cik"]),
        "extraction_method": "sec_companyfacts_json",
        "confidence_grade": "A",
        "notes": "SEC companyfacts JSON fetched for capex, operating cash flow, and revenue facts.",
    }
