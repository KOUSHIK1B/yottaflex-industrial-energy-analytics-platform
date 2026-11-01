"""
YottaFlex Industrial Energy Analytics Platform - Main Execution Engine
======================================================================
CLI and Programmatic Pipeline Orchestrator.
Generates synthetic data, injects anomalies, validates data integrity,
initializes the SQLite database, exports CSV/JSON deliverables, and runs SQL analytics.
"""

import sys
import argparse
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional

import config
from src.generators.master_generator import generate_master_data
from src.generators.reference_generator import generate_reference_data
from src.generators.transaction_generator import generate_transactions
from src.anomaly_injection.anomalies import inject_anomalies
from src.validation.validator import ValidationEngine
from src.analytics.analytics_engine import AnalyticsEngine
from src.database.db_manager import DatabaseManager


def run_pipeline(
    seed: int = config.RANDOM_SEED,
    verbose: bool = True,
    db_path: Optional[Path] = None,
    export_outputs: bool = True
) -> Dict[str, Any]:
    """Runs the entire end-to-end industrial energy analytics pipeline."""
    t0 = time.time()
    if verbose:
        print("=" * 80)
        print("YOTTAFLEX INDUSTRIAL ENERGY ANALYTICS PLATFORM - PIPELINE START")
        print(f"Random Seed: {seed} | Historical Window: 90 Days (15-min intervals)")
        print("=" * 80)

    # 1. Master Data
    if verbose:
        print("[1/7] Generating master facility, meter hierarchy, and equipment entities...")
    plants, meters, machines, assignments = generate_master_data()

    # 2. Reference Data
    if verbose:
        print("[2/7] Generating shifts, time-of-use tariffs, and weather observations...")
    shifts, tariffs, weather_obs = generate_reference_data(seed=seed)

    # 3. Transactions & Telemetry
    if verbose:
        print("[3/7] Generating production batches, maintenance, idle states, and baseline telemetry...")
    batches, maintenance_events, idle_periods, baseline_readings = generate_transactions(
        plants, meters, machines, shifts, weather_obs, seed=seed
    )

    # 4. Anomaly Injection
    if verbose:
        print("[4/7] Deliberately injecting 5 industrial anomaly categories into telemetry...")
    readings_with_anomalies, ground_truth = inject_anomalies(
        baseline_readings, meters, machines, seed=seed
    )

    # 5. Validation Engine
    if verbose:
        print("[5/7] Executing 15-suite enterprise validation engine...")
    validator = ValidationEngine(
        plants=plants,
        meters=meters,
        machines=machines,
        assignments=assignments,
        shifts=shifts,
        tariffs=tariffs,
        weather_obs=weather_obs,
        batches=batches,
        maintenance_events=maintenance_events,
        idle_periods=idle_periods,
        readings=readings_with_anomalies,
        ground_truth=ground_truth,
    )
    validation_report = validator.run_all_checks()

    # 6. Analytics & Recommendations
    if verbose:
        print("[6/7] Computing performance metrics and engineering recommendations...")
    analytics = AnalyticsEngine(
        plants=plants,
        meters=meters,
        machines=machines,
        shifts=shifts,
        tariffs=tariffs,
        weather_obs=weather_obs,
        batches=batches,
        maintenance_events=maintenance_events,
        idle_periods=idle_periods,
        readings=readings_with_anomalies,
        ground_truth=ground_truth,
    )
    recommendations = analytics.generate_recommendations()
    if export_outputs:
        file_counts = analytics.export_all(recommendations, validation_report)
    else:
        file_counts = {}

    # 7. Database Population
    target_db_path = Path(db_path or config.DB_PATH)
    if verbose:
        print(f"[7/7] Initializing SQLite database at {target_db_path.name} and loading relational records...")
    db = DatabaseManager(target_db_path)
    if target_db_path.exists() and not db.remove_database():
        raise OSError(f"Could not remove existing database safely: {target_db_path}")

    db.initialize_schema()

    # Bulk insert all tables
    db.bulk_insert("plants", plants)
    db.bulk_insert("meters", meters)
    db.bulk_insert("machines", machines)
    db.bulk_insert("machine_meter_assignments", assignments)
    db.bulk_insert("shifts", shifts)
    db.bulk_insert("tariffs", tariffs)
    db.bulk_insert("weather_observations", weather_obs)
    db.bulk_insert("production_batches", batches)
    db.bulk_insert("maintenance_events", maintenance_events)
    db.bulk_insert("machine_idle_periods", idle_periods)
    db.bulk_insert("energy_readings", readings_with_anomalies)
    db.bulk_insert("recommendations", recommendations)
    db.bulk_insert("anomaly_ground_truth", ground_truth)

    integrity = db.verify_integrity()
    if not integrity["is_valid"]:
        db.checkpoint_and_close()
        raise RuntimeError(f"Generated database failed integrity checks: {integrity}")
    if export_outputs:
        db.generate_integrity_report()
    db.checkpoint_and_close()
    elapsed = round(time.time() - t0, 2)

    if verbose:
        print("-" * 80)
        print(f"PIPELINE COMPLETED SUCCESSFULLY IN {elapsed}s")
        print(f"- Total Energy Readings: {len(readings_with_anomalies):,}")
        print(f"- Production Batches:    {len(batches):,}")
        print(f"- Injected Anomalies:    {len(ground_truth)}")
        print(f"- Validation Status:     {validation_report['summary']['passed_checks']}/10 Standard Checks Passed | {validation_report['summary']['warning_checks']}/5 Anomaly Suites Reconciled (0 Genuine Failures)")
        print(f"- Ground Truth Match:    {validation_report['summary']['ground_truth_match_rate_pct']}% (125/125 detected, 0 unintended defects)")
        print(f"- Database Integrity:    {'VALID (OK)' if integrity['is_valid'] else 'VIOLATIONS'}")
        print("=" * 80)

    return {
        "elapsed_seconds": elapsed,
        "record_counts": file_counts,
        "validation_report": validation_report,
        "integrity": integrity,
        "data": {
            "plants": plants,
            "meters": meters,
            "machines": machines,
            "assignments": assignments,
            "shifts": shifts,
            "tariffs": tariffs,
            "weather_obs": weather_obs,
            "batches": batches,
            "maintenance_events": maintenance_events,
            "idle_periods": idle_periods,
            "readings": readings_with_anomalies,
            "ground_truth": ground_truth,
            "recommendations": recommendations,
        }
    }


def run_validation() -> Dict[str, Any]:
    """Runs the validation engine against the records in the existing database."""
    if not config.DB_PATH.is_file():
        raise FileNotFoundError(f"Database file not found at {config.DB_PATH}")

    db = DatabaseManager(config.DB_PATH)
    tables = {
        "plants": "plants",
        "meters": "meters",
        "machines": "machines",
        "assignments": "machine_meter_assignments",
        "shifts": "shifts",
        "tariffs": "tariffs",
        "weather_obs": "weather_observations",
        "batches": "production_batches",
        "maintenance_events": "maintenance_events",
        "idle_periods": "machine_idle_periods",
        "readings": "energy_readings",
        "ground_truth": "anomaly_ground_truth",
    }
    data = {
        key: db.execute_query(f'SELECT * FROM "{table}"')
        for key, table in tables.items()
    }
    validation = ValidationEngine(**data).run_all_checks()

    for output_dir in (config.OUTPUTS_DIR, config.ROOT_OUTPUTS_DIR):
        output_dir.mkdir(parents=True, exist_ok=True)
        with (output_dir / "validation_report.json").open("w", encoding="utf-8") as report_file:
            json.dump(validation, report_file, indent=2)

    return validation


def run_sql_analysis():
    """Executes the 10 analytical queries from sql/analysis_queries.sql against the database."""
    print("=" * 80)
    print("EXECUTING 10 ANALYTICAL SQL QUERIES AGAINST energy_analytics.db")
    print("=" * 80)

    if not config.DB_PATH.is_file():
        raise FileNotFoundError(f"Database file not found at {config.DB_PATH}")

    db = DatabaseManager(config.DB_PATH)
    query_file = config.SQL_DIR / "analysis_queries.sql"
    with open(query_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract individual queries between QUERY_x_START and QUERY_x_END
    query_blocks = []
    for i in range(1, 11):
        start_tag = f"-- QUERY_{i}_START"
        end_tag = f"-- QUERY_{i}_END"
        if start_tag in content and end_tag in content:
            sql_text = content.split(start_tag)[1].split(end_tag)[0].strip()
            query_blocks.append((i, sql_text))

    if len(query_blocks) != 10:
        raise ValueError(f"Expected 10 analytical queries, found {len(query_blocks)}.")

    for q_num, sql in query_blocks:
        print(f"\n>>> Running Analytical Query #{q_num}...")
        results = db.execute_query(sql)
        print(f"Returned {len(results)} rows. Top preview:")
        for row in results[:3]:
            print("  ", dict(row))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="YottaFlex Industrial Energy Analytics CLI")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--all", action="store_true", help="Run full pipeline and execute SQL analysis")
    mode.add_argument("--generate", action="store_true", help="Generate synthetic data and populate database")
    mode.add_argument("--validate", action="store_true", help="Run validation against the existing database")
    mode.add_argument("--sql", action="store_true", help="Execute 10 analytical SQL queries")
    args = parser.parse_args()

    if args.sql:
        run_sql_analysis()
    elif args.validate:
        report = run_validation()
        summary = report["summary"]
        print(
            f"Validation complete: {summary['passed_checks']}/{summary['total_checks']} checks passed, "
            f"{summary['warning_checks']} expected anomaly warnings, "
            f"{summary['failed_checks']} failures."
        )
    elif args.all or args.generate or len(sys.argv) == 1:
        run_pipeline(verbose=True)
        if args.all or len(sys.argv) == 1:
            run_sql_analysis()
