import json

from ai_economics_cockpit.cli import cmd_all
from ai_economics_cockpit.config import PROCESSED_DIR


def test_payload_schema():
    cmd_all()
    payload = json.loads((PROCESSED_DIR / "dashboard_payload.json").read_text())
    required = {
        "asof_date",
        "stress_index",
        "pillar_scores",
        "metric_catalog",
        "latest_metrics",
        "time_series",
        "event_log",
        "source_registry",
        "warnings",
        "data_quality",
        "falsification_indicators",
        "validation_indicators",
    }
    assert required.issubset(payload)

