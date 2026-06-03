from ai_economics_cockpit.config import load_metric_catalog
from ai_economics_cockpit.validate.schemas import validate_metric_catalog


def test_metric_catalog_schema():
    metrics = load_metric_catalog()
    assert metrics
    assert validate_metric_catalog(metrics) == []

