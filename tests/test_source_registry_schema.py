from ai_economics_cockpit.config import load_source_registry
from ai_economics_cockpit.validate.schemas import validate_source_registry


def test_source_registry_schema():
    sources = load_source_registry()
    assert sources
    assert validate_source_registry(sources) == []

