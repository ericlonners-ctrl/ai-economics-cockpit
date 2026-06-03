import pandas as pd

from ai_economics_cockpit.scoring.score import score_metrics


def test_scoring_keeps_multiple_entities_for_same_metric():
    observations = pd.DataFrame(
        [
            {
                "metric_id": "capex_to_revenue",
                "metric_name": "Capex / revenue",
                "pillar": "hyperscaler_capex",
                "entity": "Entity A",
                "observation_date": "2026-03-31",
                "value": 12.0,
                "unit": "%",
                "frequency": "quarterly",
                "source_id": "microsoft_sec_filings",
                "confidence_grade": "A",
                "is_estimate": False,
                "estimate_method": "",
                "vintage": "2026-06-03",
                "notes": "",
            },
            {
                "metric_id": "capex_to_revenue",
                "metric_name": "Capex / revenue",
                "pillar": "hyperscaler_capex",
                "entity": "Entity B",
                "observation_date": "2026-03-31",
                "value": 28.0,
                "unit": "%",
                "frequency": "quarterly",
                "source_id": "amazon_sec_filings",
                "confidence_grade": "A",
                "is_estimate": False,
                "estimate_method": "",
                "vintage": "2026-06-03",
                "notes": "",
            },
        ]
    )
    metric_scores, _, _, _ = score_metrics(observations, asof_date="2026-06-03")
    scored = metric_scores[metric_scores["metric_id"] == "capex_to_revenue"]
    assert set(scored["entity"]) == {"Entity A", "Entity B"}

