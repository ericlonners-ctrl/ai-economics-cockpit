from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd

from .config import DB_PATH, ensure_dirs


def connect(path: Path = DB_PATH) -> duckdb.DuckDBPyConnection:
    ensure_dirs()
    return duckdb.connect(str(path))


def initialize_database(path: Path = DB_PATH) -> None:
    con = connect(path)
    con.execute(
        """
        create table if not exists source_registry (
          source_id varchar, source_name varchar, source_type varchar, url varchar,
          entity varchar, pillar varchar, refresh_frequency varchar, confidence_grade varchar,
          parser_type varchar, active boolean, notes varchar
        )
        """
    )
    con.execute(
        """
        create table if not exists raw_observations (
          observation_id varchar, source_id varchar, extracted_at varchar, observation_date date,
          entity varchar, metric_id varchar, raw_value varchar, raw_unit varchar, raw_text varchar,
          source_url varchar, extraction_method varchar, confidence_grade varchar, notes varchar
        )
        """
    )
    con.execute(
        """
        create table if not exists metric_observations (
          metric_id varchar, metric_name varchar, pillar varchar, entity varchar, observation_date date,
          value double, unit varchar, frequency varchar, source_id varchar, confidence_grade varchar,
          is_estimate boolean, estimate_method varchar, vintage varchar, notes varchar
        )
        """
    )
    con.execute(
        """
        create table if not exists metric_catalog (
          metric_id varchar, metric_name varchar, pillar varchar, description varchar, unit varchar,
          directionality varchar, green_threshold double, amber_threshold double, red_threshold double,
          transform varchar, weight double, required boolean, data_quality_rule varchar
        )
        """
    )
    con.execute(
        """
        create table if not exists event_log (
          event_id varchar, event_date date, entity varchar, pillar varchar, event_type varchar,
          title varchar, summary varchar, thesis_impact varchar, severity integer, confidence_grade varchar,
          source_id varchar, source_url varchar, notes varchar
        )
        """
    )
    con.execute(
        """
        create table if not exists pillar_scores (
          asof_date date, pillar varchar, raw_score double, confidence_adjusted_score double,
          data_coverage double, stale_metric_count integer, notes varchar
        )
        """
    )
    con.execute(
        """
        create table if not exists stress_index (
          asof_date date, ai_economic_stress_index double, enterprise_roi_score double,
          token_cost_score double, model_lab_score double, hyperscaler_capex_score double,
          infra_financing_score double, data_coverage double, average_confidence double, notes varchar
        )
        """
    )
    con.close()


def replace_table(con: duckdb.DuckDBPyConnection, name: str, df: pd.DataFrame) -> None:
    con.execute(f"delete from {name}")
    if not df.empty:
        con.register("_tmp_df", df)
        con.execute(f"insert into {name} select * from _tmp_df")
        con.unregister("_tmp_df")

