import pandas as pd

from ai_economics_cockpit.scoring.score import score_metrics


def test_missing_required_metrics_warn_and_reduce_coverage():
    metric_scores, pillar_scores, stress, warnings = score_metrics(pd.DataFrame())
    assert metric_scores.empty
    assert any(w["type"] == "missing_required_metric" for w in warnings)
    assert stress.iloc[0]["data_coverage"] == 0
    assert (pillar_scores["data_coverage"] == 0).any()

