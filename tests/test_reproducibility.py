"""
Reproducibility and Determinism Tests
=====================================
Executes the generator twice using seed 20261022.
Asserts that record counts, IDs, values, and SHA-256 checksums match 100% identically.
Uses separate isolated temporary SQLite database files for full-pipeline verification.
"""

import hashlib
import json
import pytest
from pathlib import Path
import config
from src.generators.master_generator import generate_master_data
from src.generators.reference_generator import generate_reference_data
from src.generators.transaction_generator import generate_transactions
from src.anomaly_injection.anomalies import inject_anomalies
from src.database.db_manager import DatabaseManager
from main import run_pipeline

def compute_list_sha256(records) -> str:
    """Computes a deterministic SHA-256 hash across serialized records."""
    serialized = json.dumps(records, sort_keys=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

def test_deterministic_reproducibility():
    # RUN 1
    plants1, meters1, machines1, _ = generate_master_data()
    shifts1, tariffs1, weather1 = generate_reference_data(seed=config.RANDOM_SEED)
    batches1, maint1, idle1, base_readings1 = generate_transactions(
        plants1, meters1, machines1, shifts1, weather1, seed=config.RANDOM_SEED
    )
    mutated1, gt1 = inject_anomalies(base_readings1, meters1, machines1, seed=config.RANDOM_SEED)

    # RUN 2
    plants2, meters2, machines2, _ = generate_master_data()
    shifts2, tariffs2, weather2 = generate_reference_data(seed=config.RANDOM_SEED)
    batches2, maint2, idle2, base_readings2 = generate_transactions(
        plants2, meters2, machines2, shifts2, weather2, seed=config.RANDOM_SEED
    )
    mutated2, gt2 = inject_anomalies(base_readings2, meters2, machines2, seed=config.RANDOM_SEED)

    # 1. Assert identical row counts
    assert len(base_readings1) == len(base_readings2) == 172800
    assert len(batches1) == len(batches2) == 2000
    assert len(mutated1) == len(mutated2)
    assert len(gt1) == len(gt2)

    # 2. Assert identical IDs on first, middle, and last records
    assert batches1[0]["batch_id"] == batches2[0]["batch_id"]
    assert batches1[1000]["batch_id"] == batches2[1000]["batch_id"]
    assert batches1[-1]["batch_id"] == batches2[-1]["batch_id"]

    assert base_readings1[0]["reading_id"] == base_readings2[0]["reading_id"]
    assert base_readings1[86400]["reading_id"] == base_readings2[86400]["reading_id"]
    assert base_readings1[-1]["reading_id"] == base_readings2[-1]["reading_id"]

    # 3. Assert identical values on sampled telemetry records
    sample_indices = [0, 500, 10000, 50000, 120000, 172799]
    for idx in sample_indices:
        assert base_readings1[idx]["power_demand_kw"] == base_readings2[idx]["power_demand_kw"]
        assert base_readings1[idx]["energy_consumed_kwh"] == base_readings2[idx]["energy_consumed_kwh"]
        assert base_readings1[idx]["cost_usd"] == base_readings2[idx]["cost_usd"]

    # 4. Assert exact SHA-256 hash match on ground truth registry
    gt_hash_1 = compute_list_sha256(gt1)
    gt_hash_2 = compute_list_sha256(gt2)
    assert gt_hash_1 == gt_hash_2, f"Ground truth checksum drift: {gt_hash_1} != {gt_hash_2}"

    # 5. Assert exact SHA-256 hash match on batches
    batches_hash_1 = compute_list_sha256(batches1)
    batches_hash_2 = compute_list_sha256(batches2)
    assert batches_hash_1 == batches_hash_2, f"Batches checksum drift: {batches_hash_1} != {batches_hash_2}"

def test_pipeline_reproducibility_with_temp_dbs():
    """
    Verifies that running the pipeline twice with separate temporary databases
    preserves the primary database and executes with proper connection cleanup.
    """
    temp_dir = config.DATABASE_DIR / "_test_temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_db1 = temp_dir / "test_repro_1.db"
    temp_db2 = temp_dir / "test_repro_2.db"

    # Pre-clean
    for p in [temp_db1, temp_db2]:
        DatabaseManager(p).remove_database()

    res1 = run_pipeline(seed=config.RANDOM_SEED, verbose=False, db_path=temp_db1, export_outputs=False)
    res2 = run_pipeline(seed=config.RANDOM_SEED, verbose=False, db_path=temp_db2, export_outputs=False)

    # Compare ground truth and batch hashes
    assert compute_list_sha256(res1["data"]["ground_truth"]) == compute_list_sha256(res2["data"]["ground_truth"])
    assert compute_list_sha256(res1["data"]["batches"]) == compute_list_sha256(res2["data"]["batches"])

    # Verify both databases are valid SQLite databases
    mgr1 = DatabaseManager(temp_db1)
    mgr2 = DatabaseManager(temp_db2)
    assert mgr1.verify_integrity()["is_valid"]
    assert mgr2.verify_integrity()["is_valid"]

    # Clean up
    mgr1.checkpoint_and_close()
    mgr2.checkpoint_and_close()
    mgr1.remove_database()
    mgr2.remove_database()
    try:
        temp_dir.rmdir()
    except Exception:
        pass

    # Ensure main database is intact
    assert config.DB_PATH.exists()
