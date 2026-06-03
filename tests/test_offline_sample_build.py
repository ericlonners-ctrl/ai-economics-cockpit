from ai_economics_cockpit.cli import cmd_all
from ai_economics_cockpit.config import DB_PATH, PROCESSED_DIR


def test_offline_sample_build():
    cmd_all()
    assert DB_PATH.exists()
    assert (PROCESSED_DIR / "latest_metric_snapshot.parquet").exists()
    assert (PROCESSED_DIR / "latest_scores.parquet").exists()
    assert (PROCESSED_DIR / "dashboard_payload.json").exists()

