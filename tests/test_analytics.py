"""
Analytical SQL Queries and Deliverable Exports Tests
====================================================
Tests that all 10 analytical SQL queries execute without error and produce valid results,
and validates that all required CSV, JSON, and database deliverables are generated.
"""

import os
from pathlib import Path
import pytest
import config
from src.database.db_manager import DatabaseManager

@pytest.fixture(scope="module")
def db():
    return DatabaseManager(config.DB_PATH)

def test_all_10_sql_queries_execute(db):
    query_file = config.SQL_DIR / "analysis_queries.sql"
    assert query_file.exists(), "analysis_queries.sql file is missing"
    
    with open(query_file, "r", encoding="utf-8") as f:
        content = f.read()

    executed_queries = 0
    for i in range(1, 11):
        start_tag = f"-- QUERY_{i}_START"
        end_tag = f"-- QUERY_{i}_END"
        assert start_tag in content, f"Missing {start_tag}"
        assert end_tag in content, f"Missing {end_tag}"

        sql = content.split(start_tag)[1].split(end_tag)[0].strip()
        assert len(sql) > 0, f"Query #{i} is empty"

        results = db.execute_query(sql)
        assert isinstance(results, list)
        assert len(results) > 0, f"Query #{i} returned 0 rows"
        executed_queries += 1

    assert executed_queries == 10

def test_query_1_machine_ranking(db):
    # Query 1: Top energy consuming machines
    query = """
    WITH facility_total AS (
        SELECT SUM(energy_consumed_kwh) as plant_total_kwh
        FROM energy_readings
        WHERE machine_id IS NOT NULL AND is_anomaly = 0
    )
    SELECT 
        m.machine_id,
        m.name AS machine_name,
        ROUND(SUM(r.energy_consumed_kwh), 2) AS total_energy_kwh
    FROM machines m
    JOIN energy_readings r ON m.machine_id = r.machine_id
    CROSS JOIN facility_total f
    WHERE r.is_anomaly = 0
    GROUP BY m.machine_id, m.name, f.plant_total_kwh
    ORDER BY total_energy_kwh DESC;
    """
    rows = db.execute_query(query)
    assert len(rows) == 16
    # Verify sorted descending
    energies = [r["total_energy_kwh"] for r in rows]
    assert energies == sorted(energies, reverse=True)

def test_query_1_machine_share_uses_main_incomer(db):
    query_file = config.SQL_DIR / "analysis_queries.sql"
    content = query_file.read_text(encoding="utf-8")
    sql = content.split("-- QUERY_1_START")[1].split("-- QUERY_1_END")[0].strip()
    rows = db.execute_query(sql)

    totals = db.execute_query("""
        SELECT
            SUM(CASE WHEN r.machine_id IS NOT NULL THEN r.energy_consumed_kwh ELSE 0 END) AS machine_kwh,
            SUM(CASE WHEN m.meter_type = 'MAIN_INCOMER' THEN r.energy_consumed_kwh ELSE 0 END) AS facility_kwh
        FROM energy_readings r
        JOIN meters m ON r.meter_id = m.meter_id
        WHERE r.is_anomaly = 0
    """)[0]
    expected_pct = 100.0 * totals["machine_kwh"] / totals["facility_kwh"]
    actual_pct = sum(row["pct_of_total_consumption"] for row in rows)
    assert abs(actual_pct - expected_pct) < 0.05

def test_query_5_assigns_each_reading_to_one_batch(db):
    query_file = config.SQL_DIR / "analysis_queries.sql"
    content = query_file.read_text(encoding="utf-8")
    sql = content.split("-- QUERY_5_START")[1].split("-- QUERY_5_END")[0].strip()
    rows = db.execute_query(sql)
    batch_totals = db.execute_query("""
        SELECT COUNT(*) AS batch_count, SUM(actual_good_units) AS good_units
        FROM production_batches
    """)[0]
    assert sum(row["total_batches_run"] for row in rows) == batch_totals["batch_count"]
    assert sum(row["total_good_units_produced"] for row in rows) == batch_totals["good_units"]

    expected_kwh = db.execute_query("""
        WITH assigned_readings AS (
            SELECT
                r.reading_id,
                r.energy_consumed_kwh,
                ROW_NUMBER() OVER (
                    PARTITION BY r.reading_id
                    ORDER BY b.start_timestamp DESC, b.batch_id
                ) AS batch_rank
            FROM production_batches b
            JOIN energy_readings r ON b.machine_id = r.machine_id
                AND r.timestamp >= b.start_timestamp
                AND r.timestamp <= b.end_timestamp
            WHERE r.is_anomaly = 0
        )
        SELECT SUM(energy_consumed_kwh) AS total_kwh
        FROM assigned_readings
        WHERE batch_rank = 1
    """)[0]["total_kwh"]
    actual_kwh = sum(row["total_production_kwh"] for row in rows)
    assert abs(actual_kwh - expected_kwh) < 0.02

def test_query_4_peak_demand_within_capacity(db):
    # Peak demand at Main Incomer should not exceed grid connection threshold
    query = """
    SELECT ROUND(MAX(r.power_demand_kw), 2) as max_peak_kw
    FROM energy_readings r
    JOIN meters m ON r.meter_id = m.meter_id
    WHERE r.is_anomaly = 0 AND m.meter_type = 'MAIN_INCOMER';
    """
    row = db.execute_query(query)[0]
    peak_kw = row["max_peak_kw"]
    assert peak_kw > 0
    # Contracted capacity is 2,500 kW
    assert peak_kw <= 2500.0, f"Peak demand {peak_kw} kW exceeded contracted 2,500 kW threshold"

def test_all_deliverable_files_exist():
    required_files = [
        config.MASTER_DIR / "plants.csv",
        config.MASTER_DIR / "meters.csv",
        config.MASTER_DIR / "machines.csv",
        config.TRANSACTIONS_DIR / "energy_readings.csv",
        config.TRANSACTIONS_DIR / "production_batches.csv",
        config.REFERENCE_DIR / "shifts.csv",
        config.REFERENCE_DIR / "tariffs.csv",
        config.REFERENCE_DIR / "weather_observations.csv",
        config.EVENTS_DIR / "maintenance_events.csv",
        config.GROUND_TRUTH_DIR / "ground_truth.csv",
        config.GROUND_TRUTH_DIR / "ground_truth.json",
        config.OUTPUTS_DIR / "energy_analytics.csv",
        config.OUTPUTS_DIR / "machine_performance.csv",
        config.OUTPUTS_DIR / "peak_demand.csv",
        config.OUTPUTS_DIR / "energy_waste.csv",
        config.OUTPUTS_DIR / "recommendations.csv",
        config.OUTPUTS_DIR / "validation_report.json",
        config.SQL_DIR / "schema.sql",
        config.SQL_DIR / "seed.sql",
        config.SQL_DIR / "analysis_queries.sql",
        config.DOCS_DIR / "data_dictionary.md",
        config.DOCS_DIR / "business_rules.md",
        config.DOCS_DIR / "architecture.md",
        config.DOCS_DIR / "er_diagram.md",
        config.DOCS_DIR / "final_quality_report.md",
        config.ROOT_OUTPUTS_DIR / "reproducibility_report.json",
        config.ROOT_OUTPUTS_DIR / "final_quality_report.json",
        config.BASE_DIR / "README.md",
    ]

    for f_path in required_files:
        assert f_path.exists(), f"Missing required deliverable file: {f_path}"
        assert f_path.stat().st_size > 0, f"File is empty: {f_path}"

def test_query_7_no_join_multiplication(db):
    """
    Regression test for Issue 3: Ensures Query 7 does not multiply production batches.
    Total batches across shifts must equal exactly 2,000.
    """
    query_file = config.SQL_DIR / "analysis_queries.sql"
    with open(query_file, "r", encoding="utf-8") as f:
        content = f.read()

    sql = content.split("-- QUERY_7_START")[1].split("-- QUERY_7_END")[0].strip()
    rows = db.execute_query(sql)

    assert len(rows) == 3, f"Expected 3 shifts, got {len(rows)}"
    total_batches = sum(r["batches_processed"] for r in rows)
    assert total_batches == 2000, f"Join multiplication detected! Expected 2,000 batches, got {total_batches}"

    # Also verify total units produced matches distinct batches table sum
    db_units = db.execute_query("SELECT SUM(actual_good_units) as tot FROM production_batches")[0]["tot"]
    query_units = sum(r["total_units_produced"] for r in rows)
    assert query_units == db_units, f"Good units mismatch: query {query_units} != db {db_units}"

    main_incomer_kwh = db.execute_query("""
        SELECT SUM(r.energy_consumed_kwh) AS total_kwh
        FROM energy_readings r
        JOIN meters m ON r.meter_id = m.meter_id
        WHERE r.is_anomaly = 0 AND m.meter_type = 'MAIN_INCOMER'
    """)[0]["total_kwh"]
    shift_kwh = sum(row["total_shift_kwh"] for row in rows)
    assert abs(shift_kwh - main_incomer_kwh) < 0.02

    unique_batch_kwh = db.execute_query("""
        WITH assigned_readings AS (
            SELECT
                r.reading_id,
                r.energy_consumed_kwh,
                ROW_NUMBER() OVER (
                    PARTITION BY r.reading_id
                    ORDER BY b.start_timestamp DESC, b.batch_id
                ) AS batch_rank
            FROM production_batches b
            JOIN energy_readings r ON b.machine_id = r.machine_id
                AND r.timestamp >= b.start_timestamp
                AND r.timestamp <= b.end_timestamp
            WHERE r.is_anomaly = 0
        )
        SELECT SUM(energy_consumed_kwh) AS total_kwh
        FROM assigned_readings
        WHERE batch_rank = 1
    """)[0]["total_kwh"]
    shift_machine_kwh = sum(row["machine_production_kwh"] for row in rows)
    assert abs(shift_machine_kwh - unique_batch_kwh) < 0.02

def test_query_4_meter_hierarchy_aggregation(db):
    """
    Regression test for Issue 4: Ensures Query 4 reports correct plant demand,
    active meter counts, and feeder/machine breakdown across the hierarchy.
    """
    query_file = config.SQL_DIR / "analysis_queries.sql"
    with open(query_file, "r", encoding="utf-8") as f:
        content = f.read()

    sql = content.split("-- QUERY_4_START")[1].split("-- QUERY_4_END")[0].strip()
    rows = db.execute_query(sql)

    assert len(rows) == 20
    top_row = rows[0]
    # Verify active meters reporting across plant
    assert top_row["active_meter_count"] == 20, f"Expected 20 active meters, got {top_row['active_meter_count']}"
    # Verify plant demand equals Main Incomer demand (~1045 kW)
    assert top_row["plant_total_demand_kw"] > 1000.0
    assert top_row["plant_total_demand_kw"] <= 2500.0
    # Machine submeters demand must be positive and less than plant demand (due to busbar losses)
    assert 0 < top_row["machine_submeters_demand_kw"] < top_row["plant_total_demand_kw"]

def test_duplicate_reading_isolation(db):
    """
    Regression test for Issue 2: Confirms duplicate readings (Category 4) are flagged
    with is_anomaly = 1 and excluded from clean analytics.
    172,800 baseline readings + 20 injected duplicate readings = 172,820 total readings.
    125 total anomaly readings (105 in-place + 20 duplicates) have is_anomaly = 1.
    172,820 - 125 = 172,695 clean baseline readings with is_anomaly = 0.
    """
    total_readings = db.execute_query("SELECT COUNT(*) as c FROM energy_readings")[0]["c"]
    assert total_readings == 172820, f"Expected 172,820 total readings, got {total_readings}"

    anomaly_readings = db.execute_query("SELECT COUNT(*) as c FROM energy_readings WHERE is_anomaly = 1")[0]["c"]
    assert anomaly_readings == 125, f"Expected 125 anomaly readings, got {anomaly_readings}"

    clean_readings = db.execute_query("SELECT COUNT(*) as c FROM energy_readings WHERE is_anomaly = 0")[0]["c"]
    assert clean_readings == 172695, f"Expected 172,695 clean baseline readings, got {clean_readings}"

    dup_readings = db.execute_query("SELECT COUNT(*) as c FROM energy_readings WHERE is_anomaly = 1 AND anomaly_category = 'DUPLICATE_READING'")[0]["c"]
    assert dup_readings == 20, f"Expected 20 duplicate readings, got {dup_readings}"
