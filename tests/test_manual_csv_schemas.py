from ai_economics_cockpit.ingest.manual import MANUAL_DIR, MANUAL_FILES, ensure_manual_templates
from ai_economics_cockpit.validate.schemas import validate_manual_csv


def test_manual_csv_schemas():
    ensure_manual_templates()
    for name in MANUAL_FILES:
        assert validate_manual_csv(MANUAL_DIR / name) == []

