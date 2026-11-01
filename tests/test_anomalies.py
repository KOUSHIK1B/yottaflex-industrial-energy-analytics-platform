"""
Anomaly Injection & Ground Truth Registry Tests
================================================
Verifies that all 5 required industrial anomaly categories are injected,
recorded in ground truth with unique IDs, and detectable by validation rules.
"""

import pytest
import config
from src.generators.master_generator import generate_master_data
from src.generators.reference_generator import generate_reference_data
from src.generators.transaction_generator import generate_transactions
from src.anomaly_injection.anomalies import inject_anomalies

@pytest.fixture(scope="module")
def anomaly_data():
    plants, meters, machines, _ = generate_master_data()
    shifts, tariffs, weather = generate_reference_data(seed=config.RANDOM_SEED)
    _, _, _, baseline_readings = generate_transactions(
        plants, meters, machines, shifts, weather, seed=config.RANDOM_SEED
    )
    mutated_readings, ground_truth = inject_anomalies(
        baseline_readings, meters, machines, seed=config.RANDOM_SEED
    )
    return mutated_readings, ground_truth

def test_anomaly_five_categories_presence(anomaly_data):
    _, ground_truth = anomaly_data
    
    categories = {g["category_name"] for g in ground_truth}
    expected_categories = {
        "METER_SUM_MISMATCH",
        "KW_KWH_CONFUSION",
        "TARIFF_TZ_MISMATCH",
        "DUPLICATE_READING",
        "HIERARCHY_VIOLATION",
    }
    assert expected_categories.issubset(categories)

def test_anomaly_ground_truth_fields(anomaly_data):
    _, ground_truth = anomaly_data
    seen_ids = set()

    for g in ground_truth:
        # ID convention: ANO-2026-000001
        ano_id = g["anomaly_id"]
        assert ano_id.startswith("ANO-2026-")
        assert ano_id not in seen_ids
        seen_ids.add(ano_id)

        assert g["category_id"] in {1, 2, 3, 4, 5}
        assert g["severity"] in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
        assert len(g["expected_detection_rule"]) > 0
        assert len(g["rationale"]) > 0
        assert len(g["original_value"]) > 0
        assert len(g["injected_value"]) > 0

def test_anomalies_flagged_in_telemetry(anomaly_data):
    mutated_readings, ground_truth = anomaly_data
    flagged = [r for r in mutated_readings if r["is_anomaly"] == 1]
    
    # Check that flagged records in telemetry correspond to ground truth count
    assert len(flagged) >= len(ground_truth)

def test_anomaly_exact_injection_counts(anomaly_data):
    """
    Regression test for Issue 1 & Issue 6: Verifies strictly 125 injected anomalies
    across the 5 mandated categories with exact counts.
    """
    _, ground_truth = anomaly_data
    assert len(ground_truth) == 125, f"Expected 125 total anomalies, got {len(ground_truth)}"

    cat_counts = {}
    for g in ground_truth:
        cname = g["category_name"]
        cat_counts[cname] = cat_counts.get(cname, 0) + 1

    assert cat_counts.get("KW_KWH_CONFUSION") == 35, f"Expected 35 KW_KWH_CONFUSION, got {cat_counts.get('KW_KWH_CONFUSION')}"
    assert cat_counts.get("TARIFF_TZ_MISMATCH") == 30, f"Expected 30 TARIFF_TZ_MISMATCH, got {cat_counts.get('TARIFF_TZ_MISMATCH')}"
    assert cat_counts.get("METER_SUM_MISMATCH") == 25, f"Expected 25 METER_SUM_MISMATCH, got {cat_counts.get('METER_SUM_MISMATCH')}"
    assert cat_counts.get("DUPLICATE_READING") == 20, f"Expected 20 DUPLICATE_READING, got {cat_counts.get('DUPLICATE_READING')}"
    assert cat_counts.get("HIERARCHY_VIOLATION") == 15, f"Expected 15 HIERARCHY_VIOLATION, got {cat_counts.get('HIERARCHY_VIOLATION')}"

def test_all_15_validation_suites_pass():
    """
    Regression test for Issue 1: Verifies that all 15 validation suites pass,
    with 125 expected anomalies detected and zero unintended defects.
    """
    from src.validation.validator import ValidationEngine
    from src.generators.master_generator import generate_master_data
    from src.generators.reference_generator import generate_reference_data
    from src.generators.transaction_generator import generate_transactions

    plants, meters, machines, assignments = generate_master_data()
    shifts, tariffs, weather = generate_reference_data(seed=config.RANDOM_SEED)
    batches, maint, idle, baseline_readings = generate_transactions(
        plants, meters, machines, shifts, weather, seed=config.RANDOM_SEED
    )
    mutated_readings, ground_truth = inject_anomalies(
        baseline_readings, meters, machines, seed=config.RANDOM_SEED
    )

    validator = ValidationEngine(
        plants=plants,
        meters=meters,
        machines=machines,
        assignments=assignments,
        shifts=shifts,
        tariffs=tariffs,
        weather_obs=weather,
        batches=batches,
        maintenance_events=maint,
        idle_periods=idle,
        readings=mutated_readings,
        ground_truth=ground_truth,
    )

    report = validator.run_all_checks()
    assert report["summary"]["total_checks"] == 15
    assert report["summary"]["passed_checks"] == 10, f"Expected 10 ordinary passed checks, got {report['summary']['passed_checks']}"
    assert report["summary"]["warning_checks"] == 5, f"Expected 5 expected anomaly warnings, got {report['summary']['warning_checks']}"
    assert report["summary"]["failed_checks"] == 0, f"Expected 0 failed checks, got {report['summary']['failed_checks']}"
    assert report["summary"]["genuine_validation_failures"] == 0
    assert report["summary"]["unintended_defect_count"] == 0
    assert report["summary"]["injected_ground_truth_count"] == 125
    assert report["summary"]["detected_anomalies_count"] == 125
    assert report["summary"]["ground_truth_match_rate_pct"] == 100.0

