import hashlib

from ai_economics_cockpit.cli import cmd_all
from ai_economics_cockpit.config import PROCESSED_DIR


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_idempotent_build():
    cmd_all()
    first = digest(PROCESSED_DIR / "dashboard_payload.json")
    cmd_all()
    second = digest(PROCESSED_DIR / "dashboard_payload.json")
    assert first == second

