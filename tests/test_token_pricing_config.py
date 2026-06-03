from ai_economics_cockpit.config import load_token_pricing_config
from ai_economics_cockpit.ingest.official_pricing import curated_token_price_rows


def test_token_pricing_config_schema():
    cfg = load_token_pricing_config()
    assert cfg["asof_date"]
    assert cfg["models"]
    required = {
        "provider",
        "model",
        "source_id",
        "source_url",
        "confidence_grade",
        "input_usd_per_mtok",
        "cached_input_usd_per_mtok",
        "output_usd_per_mtok",
    }
    for model in cfg["models"]:
        assert required.issubset(model)
        assert model["confidence_grade"] == "A"
        assert model["input_usd_per_mtok"] > 0
        assert model["output_usd_per_mtok"] > 0


def test_curated_token_pricing_emits_required_metrics():
    rows = curated_token_price_rows()
    metric_ids = {row["metric_id"] for row in rows}
    assert "openai_weighted_token_price" in metric_ids
    assert "anthropic_weighted_token_price" in metric_ids
    assert "google_weighted_token_price" in metric_ids
    assert "provider_token_price_index" in metric_ids
    assert "estimated_cost_per_agentic_task" in metric_ids
    assert all(row["source_id"] for row in rows)
    assert all(row["confidence_grade"] for row in rows)

