import json

from ai_economics_cockpit.cli import cmd_all
from ai_economics_cockpit.config import PROCESSED_DIR


def test_sample_data_warning_present():
    cmd_all()
    payload = json.loads((PROCESSED_DIR / "dashboard_payload.json").read_text())
    assert payload["data_quality"]["sample_observation_count"] > 0
    assert any(w["type"] == "sample_data_present" for w in payload["warnings"])

