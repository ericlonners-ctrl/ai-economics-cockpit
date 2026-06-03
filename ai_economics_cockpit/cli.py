from __future__ import annotations

import argparse
import os
import subprocess
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

import pandas as pd

from .build.dashboard import write_build_report, write_dashboard_assets
from .build.payload import build_payload
from .config import DB_PATH, PARQUET_DIR, PROCESSED_DIR, PROJECT_ROOT, ensure_dirs, load_metric_catalog, load_source_registry
from .db import connect, initialize_database, replace_table
from .ingest.manual import ensure_manual_templates, load_manual_data
from .ingest.official_pricing import ingest_official_pricing
from .ingest.sec_filings import ingest_sec_companyfacts
from .scoring.score import score_metrics
from .validate.rules import validate_metric_rows
from .validate.schemas import validate_metric_catalog, validate_source_registry


def main() -> None:
    parser = argparse.ArgumentParser(description="AI economics cockpit CLI")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init")
    ingest_parser = sub.add_parser("ingest")
    ingest_parser.add_argument("--manual", action="store_true")
    ingest_parser.add_argument("--sources", default="")
    sub.add_parser("build")
    sub.add_parser("validate")
    serve_parser = sub.add_parser("serve")
    serve_parser.add_argument("--port", type=int, default=8765)
    all_parser = sub.add_parser("all")
    all_parser.add_argument("--online", action="store_true", help="Include network-backed official pricing and SEC companyfacts ingestion.")
    args = parser.parse_args()

    if args.command == "init":
        cmd_init()
    elif args.command == "ingest":
        cmd_ingest(manual=args.manual, sources=args.sources)
    elif args.command == "build":
        cmd_build()
    elif args.command == "validate":
        cmd_validate()
    elif args.command == "serve":
        cmd_serve(args.port)
    elif args.command == "all":
        cmd_all(online=args.online)


def cmd_init() -> None:
    ensure_dirs()
    ensure_manual_templates()
    initialize_database()
    write_dashboard_assets()
    load_configs_into_db()
    print(f"initialized {PROJECT_ROOT}")


def load_configs_into_db() -> None:
    con = connect()
    sources = pd.DataFrame(load_source_registry())
    catalog = pd.DataFrame(load_metric_catalog())
    replace_table(con, "source_registry", sources)
    replace_table(con, "metric_catalog", catalog[["metric_id", "metric_name", "pillar", "description", "unit", "directionality", "green_threshold", "amber_threshold", "red_threshold", "transform", "weight", "required", "data_quality_rule"]])
    con.close()


def cmd_ingest(manual: bool = False, sources: str = "") -> list[dict]:
    ensure_dirs()
    initialize_database()
    load_configs_into_db()
    metric_frames: list[pd.DataFrame] = []
    raw_frames: list[pd.DataFrame] = []
    event_frames: list[pd.DataFrame] = []
    warning_text: list[str] = []
    if manual or not sources:
        metrics, events, warnings = load_manual_data()
        metric_frames.append(metrics)
        event_frames.append(events)
        warning_text.extend(warnings)
    if "official_pricing" in sources.split(","):
        metrics, raw, warnings = ingest_official_pricing()
        metric_frames.append(metrics)
        raw_frames.append(raw)
        warning_text.extend(warnings)
    if "sec_filings" in sources.split(","):
        metrics, raw, warnings = ingest_sec_companyfacts()
        metric_frames.append(metrics)
        raw_frames.append(raw)
        warning_text.extend(warnings)
    metrics_df = pd.concat([f for f in metric_frames if not f.empty], ignore_index=True) if metric_frames else pd.DataFrame()
    events_df = pd.concat([f for f in event_frames if not f.empty], ignore_index=True) if event_frames else pd.DataFrame()
    raw_df = pd.concat([f for f in raw_frames if not f.empty], ignore_index=True) if raw_frames else pd.DataFrame()
    warning_text.extend(validate_metric_rows(metrics_df))
    con = connect()
    if not metrics_df.empty:
        replace_table(con, "metric_observations", metrics_df)
    if not events_df.empty:
        replace_table(con, "event_log", events_df)
    if not raw_df.empty:
        replace_table(con, "raw_observations", raw_df)
    con.close()
    return [{"type": "ingest_warning", "metric_id": "", "pillar": "", "message": w} for w in warning_text]


def cmd_build(extra_warnings: list[dict] | None = None) -> list[dict]:
    ensure_dirs()
    initialize_database()
    con = connect()
    observations = con.execute("select * from metric_observations").fetchdf()
    events = con.execute("select * from event_log").fetchdf()
    metric_scores, pillar_scores, stress_index, warnings = score_metrics(observations)
    warnings.extend(extra_warnings or [])
    replace_table(con, "pillar_scores", pillar_scores)
    replace_table(con, "stress_index", stress_index)
    con.close()
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    PARQUET_DIR.mkdir(parents=True, exist_ok=True)
    metric_scores.to_parquet(PROCESSED_DIR / "latest_metric_snapshot.parquet", index=False)
    metric_scores.to_parquet(PARQUET_DIR / "latest_metric_snapshot.parquet", index=False)
    pillar_scores.to_parquet(PARQUET_DIR / "pillar_scores.parquet", index=False)
    stress_index.to_parquet(PROCESSED_DIR / "latest_scores.parquet", index=False)
    stress_index.to_parquet(PARQUET_DIR / "latest_scores.parquet", index=False)
    build_payload(metric_scores, pillar_scores, stress_index, events, warnings)
    write_dashboard_assets()
    return warnings


def cmd_validate() -> list[str]:
    warnings = []
    warnings.extend(validate_source_registry(load_source_registry()))
    warnings.extend(validate_metric_catalog(load_metric_catalog()))
    ensure_manual_templates()
    from .ingest.manual import MANUAL_FILES, MANUAL_DIR
    from .validate.schemas import validate_manual_csv

    for name in MANUAL_FILES:
        warnings.extend(validate_manual_csv(MANUAL_DIR / name))
    if warnings:
        for warning in warnings:
            print(warning)
        raise SystemExit(1)
    print("validation passed")
    return warnings


def cmd_all(online: bool = False) -> None:
    ingest_sources = "official_pricing,sec_filings" if online else ""
    commands = [
        "python -m ai_economics_cockpit init",
        f"python -m ai_economics_cockpit ingest --manual{' --sources official_pricing,sec_filings' if online else ''}",
        "python -m ai_economics_cockpit build",
        "python -m ai_economics_cockpit validate",
    ]
    cmd_init()
    ingest_warnings = cmd_ingest(manual=True, sources=ingest_sources)
    build_warnings = cmd_build(extra_warnings=ingest_warnings)
    try:
        cmd_validate()
        test_result = "Validation passed. The GitHub Pages workflow runs `pytest` before the online publish build; locally run `.venv/bin/pytest` for the full suite."
    except SystemExit:
        test_result = "Validation failed."
        raise
    write_build_report(commands, test_result, build_warnings)
    print(f"built {PROCESSED_DIR / 'dashboard_payload.json'}")
    print(f"database {DB_PATH}")


def cmd_serve(port: int) -> None:
    os.chdir(PROJECT_ROOT)
    handler = SimpleHTTPRequestHandler
    server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    print(f"serving http://127.0.0.1:{port}/dashboard/")
    subprocess.run(["python", "-m", "webbrowser", f"http://127.0.0.1:{port}/dashboard/"], cwd=PROJECT_ROOT, check=False)
    server.serve_forever()
