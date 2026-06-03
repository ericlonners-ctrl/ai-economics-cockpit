from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR = PROJECT_ROOT / "data"
MANUAL_DIR = DATA_DIR / "manual"
PROCESSED_DIR = DATA_DIR / "processed"
PARQUET_DIR = PROCESSED_DIR / "parquet"
DB_PATH = DATA_DIR / "ai_economics.duckdb"
DASHBOARD_DIR = PROJECT_ROOT / "dashboard"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_source_registry() -> list[dict[str, Any]]:
    return load_yaml(CONFIG_DIR / "source_registry.yaml")["sources"]


def load_metric_catalog() -> list[dict[str, Any]]:
    return load_yaml(CONFIG_DIR / "metric_catalog.yaml")["metrics"]


def load_scoring_config() -> dict[str, Any]:
    return load_yaml(CONFIG_DIR / "scoring.yaml")


def load_falsification_config() -> dict[str, Any]:
    return load_yaml(CONFIG_DIR / "falsification.yaml")


def ensure_dirs() -> None:
    for path in [DATA_DIR, MANUAL_DIR, PROCESSED_DIR, PARQUET_DIR, DASHBOARD_DIR, DASHBOARD_DIR / "assets", ARTIFACTS_DIR]:
        path.mkdir(parents=True, exist_ok=True)

