"""
Database Integrity and Schema Tests
===================================
Verifies SQLite schema creation, foreign key constraints, indexes,
and query execution against the seeded database.
"""

import sqlite3
import pytest
from pathlib import Path
import config
from src.database.db_manager import DatabaseManager

@pytest.fixture(scope="module")
def db_conn():
    db = DatabaseManager(config.DB_PATH)
    if not config.DB_PATH.exists():
        # Ensure database is generated
        from main import run_pipeline
        run_pipeline(verbose=False)
    conn = db.get_connection()
    yield conn
    conn.close()

def test_database_tables_exist(db_conn):
    cursor = db_conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = {row[0] for row in cursor.fetchall()}
    
    expected_tables = {
        "plants", "meters", "machines", "machine_meter_assignments",
        "shifts", "tariffs", "weather_observations", "production_batches",
        "energy_readings", "maintenance_events", "machine_idle_periods",
        "recommendations", "anomaly_ground_truth"
    }
    assert expected_tables.issubset(tables)

def test_foreign_key_pragmas(db_conn):
    cursor = db_conn.cursor()
    cursor.execute("PRAGMA foreign_key_check;")
    fk_violations = cursor.fetchall()
    assert len(fk_violations) == 0, f"Foreign key violations found: {fk_violations}"

def test_sqlite_integrity_check(db_conn):
    cursor = db_conn.cursor()
    cursor.execute("PRAGMA integrity_check;")
    row = cursor.fetchone()
    assert row[0] == "ok"

def test_record_counts_in_database(db_conn):
    cursor = db_conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM meters;")
    assert cursor.fetchone()[0] == 20

    cursor.execute("SELECT COUNT(*) FROM machines;")
    assert cursor.fetchone()[0] == 16

    cursor.execute("SELECT COUNT(*) FROM production_batches;")
    assert cursor.fetchone()[0] == 2000

    cursor.execute("SELECT COUNT(*) FROM energy_readings;")
    count = cursor.fetchone()[0]
    # 172,800 baseline + 20 duplicate injected anomalies = 172,820
    assert count == 172820, f"Expected 172,820 readings, got {count}"

    cursor.execute("SELECT COUNT(*) FROM anomaly_ground_truth;")
    gt_count = cursor.fetchone()[0]
    assert gt_count == 125, f"Expected 125 ground truth anomalies, got {gt_count}"

def test_recommendations_and_modeled_savings(db_conn):
    cursor = db_conn.cursor()
    cursor.execute("SELECT COUNT(*), ROUND(SUM(estimated_annual_cost_savings_usd), 2) FROM recommendations;")
    row = cursor.fetchone()
    rec_count, total_savings = row[0], row[1]
    assert rec_count == 10, f"Expected 10 recommendations, got {rec_count}"
    assert total_savings == 228848.32, f"Expected exactly $228,848.32, got {total_savings}"

    # Verify all recommendations have modeled_savings_type = 'SYNTHETIC_ESTIMATE'
    cursor.execute("SELECT DISTINCT modeled_savings_type FROM recommendations;")
    types = [r[0] for r in cursor.fetchall()]
    assert types == ["SYNTHETIC_ESTIMATE"]

