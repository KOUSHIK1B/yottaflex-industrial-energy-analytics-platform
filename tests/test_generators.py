"""
Unit and Integration Tests for Master, Reference, and Transaction Generators
===========================================================================
Verifies row counts, naming conventions, date ranges, and physical bounds.
"""

import pytest
import config
from src.generators.master_generator import generate_master_data
from src.generators.reference_generator import generate_reference_data
from src.generators.transaction_generator import generate_transactions

def test_master_data_row_counts_and_conventions():
    plants, meters, machines, assignments = generate_master_data()

    # 1 Plant
    assert len(plants) == 1
    assert plants[0]["plant_id"] == "PLT-001"
    assert plants[0]["timezone"] == "America/Chicago"

    # Exactly 20 Meters
    assert len(meters) == 20
    assert meters[0]["meter_id"] == "MTR-PLT-001-001"
    assert meters[0]["meter_type"] == "MAIN_INCOMER"
    assert meters[0]["parent_meter_id"] is None

    # Check zero-padded meter IDs MTR-PLT-001-001 to 020
    for idx, mtr in enumerate(meters, start=1):
        assert mtr["meter_id"] == f"MTR-PLT-001-{idx:03d}"
        assert mtr["voltage_rating_v"] > 0
        assert mtr["current_rating_a"] > 0

    # 16 Machines
    assert len(machines) == 16
    for idx, mch in enumerate(machines, start=1):
        assert mch["machine_id"] == f"MCH-PLT-001-{idx:03d}"
        assert mch["rated_power_kw"] > 0
        assert mch["operating_power_kw"] >= mch["standby_power_kw"]

    # 16 Bridge assignments
    assert len(assignments) == 16
    for asn in assignments:
        assert asn["allocation_percentage"] == 100.0

def test_reference_data_integrity():
    shifts, tariffs, weather = generate_reference_data(seed=config.RANDOM_SEED)

    # 3 Operating Shifts
    assert len(shifts) == 3
    assert {s["shift_id"] for s in shifts} == {"SHF-001", "SHF-002", "SHF-003"}

    # 4 Tariffs with deterministic IDs TAR-2026-001 to TAR-2026-004
    assert len(tariffs) == 4
    for idx, t in enumerate(tariffs, start=1):
        assert t["tariff_id"] == f"TAR-2026-{idx:03d}"
        assert t["rate_per_kwh_usd"] > 0

    # Weather observations: 90 days * 24 hours = 2,160
    expected_weather = config.DAYS_OF_HISTORY * 24
    assert len(weather) == expected_weather
    for w in weather:
        assert 10.0 <= w["dry_bulb_temperature_c"] <= 45.0
        assert 0.0 <= w["relative_humidity_pct"] <= 100.0
        assert w["cooling_degree_load_factor"] >= 0.0

def test_transaction_data_counts_and_physics():
    plants, meters, machines, _ = generate_master_data()
    shifts, tariffs, weather = generate_reference_data(seed=config.RANDOM_SEED)
    batches, maint, idle, readings = generate_transactions(
        plants, meters, machines, shifts, weather, seed=config.RANDOM_SEED
    )

    # 2,000 Production Batches
    assert len(batches) == 2000
    for idx, b in enumerate(batches, start=1):
        assert b["batch_id"].startswith("BATCH-2026-")
        assert b["actual_good_units"] >= 0
        assert b["actual_scrap_units"] >= 0
        assert b["actual_good_units"] + b["actual_scrap_units"] == b["planned_units"]

    # 172,800 Baseline Energy Readings (20 meters * 90 days * 96 intervals)
    expected_readings = 20 * config.DAYS_OF_HISTORY * 24 * 4
    assert len(readings) == expected_readings
    assert expected_readings == 172800

    # Maintenance and Idle events generated
    assert len(maint) > 50
    assert len(idle) > 300
