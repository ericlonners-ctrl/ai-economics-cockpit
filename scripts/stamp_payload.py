"""Stamp the built payload with a fleet-convention freshness block and mirror it.

Run AFTER `python -m ai_economics_cockpit all --online`. Kept outside the Python
build so the build itself stays byte-idempotent (tests/test_idempotent_build.py).

Adds payload["meta"] = {generatedAt (ISO-8601 UTC), asof_date, builder, ...}
and copies the stamped payload to dashboard/data/processed/ (the second copy the
static site ships). Sample/manual observations stay labelled by the build's own
warnings/data_quality fields; this script never edits values.
"""
from __future__ import annotations

import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "processed" / "dashboard_payload.json"
MIRROR = ROOT / "dashboard" / "data" / "processed" / "dashboard_payload.json"


def main() -> int:
    payload = json.loads(SRC.read_text(encoding="utf-8"))
    dq = payload.get("data_quality", {})
    payload["meta"] = {
        "cockpit": "ai-economics-cockpit",
        "generatedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "asof_date": payload.get("asof_date"),
        "builder": os.environ.get(
            "PAYLOAD_BUILDER", "python -m ai_economics_cockpit all --online (local)"
        ),
        "online_sources": ["official_pricing", "sec_filings"],
        "sample_observation_count": dq.get("sample_observation_count"),
        "note": "Manual/sample observations remain labelled via warnings + data_quality; only the build stamp and network-backed sources refresh automatically.",
    }
    text = json.dumps(payload, indent=2, sort_keys=True, default=str)
    SRC.write_text(text, encoding="utf-8")
    MIRROR.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SRC, MIRROR)
    print(f"stamped asof={payload['meta']['asof_date']} generatedAt={payload['meta']['generatedAt']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
