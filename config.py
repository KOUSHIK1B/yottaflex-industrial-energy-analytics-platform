"""
YottaFlex Industrial Energy Analytics Platform - Configuration
==============================================================
Centralized immutable parameters, constants, file paths, and seed definitions.
Ensures 100% deterministic reproducibility across pipeline runs.
"""

import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent

# Fixed random seed as mandated by specification
RANDOM_SEED: int = 20261022

# Dataset Configuration
PLANT_ID: str = "PLT-001"
PLANT_NAME: str = "YottaFlex Precision Metals & Robotics Plant #1"
PLANT_LOCATION: str = "Austin, TX (Industrial Zone North)"
TIMEZONE: str = "America/Chicago"  # UTC-5 (CDT) / UTC-6 (CST)

NUM_METERS: int = 20
NUM_MACHINES: int = 16
NUM_BATCHES: int = 2000
DAYS_OF_HISTORY: int = 90
INTERVAL_MINUTES: int = 15

# Historical time window (90 days ending 2026-10-22)
# 90 days * 24 hours * 4 intervals = 8,640 intervals per meter
# 20 meters * 8,640 intervals = 172,800 baseline energy readings
START_DATE_STR: str = "2026-07-25 00:00:00"
END_DATE_STR: str = "2026-10-22 23:45:00"

# Directories
DATA_DIR = BASE_DIR / "data"
MASTER_DIR = DATA_DIR / "master"
TRANSACTIONS_DIR = DATA_DIR / "transactions"
REFERENCE_DIR = DATA_DIR / "reference"
EVENTS_DIR = DATA_DIR / "events"
GROUND_TRUTH_DIR = DATA_DIR / "ground_truth"
OUTPUTS_DIR = DATA_DIR / "outputs"
ROOT_OUTPUTS_DIR = BASE_DIR / "outputs"
DATABASE_DIR = BASE_DIR / "database"
SQL_DIR = BASE_DIR / "sql"
DOCS_DIR = BASE_DIR / "docs"

# Database path
DB_PATH = DATABASE_DIR / "energy_analytics.db"

# Anomaly Injections Configuration (Strictly 125 Total)
ANOMALY_CONFIG = {
    "kw_kwh_confusion_count": 35,       # Category 2: kW confused with kWh (35)
    "tariff_tz_mismatch_count": 30,     # Category 3: Tariff timezone mismatch (30)
    "meter_sum_mismatch_count": 25,     # Category 1: Meter total disagrees with interval sums (25)
    "duplicate_readings_count": 20,     # Category 4: Duplicate energy readings (20)
    "hierarchy_violation_count": 15,    # Category 5: Energy assigned to machine outside meter hierarchy (15)
}

# Ensure all directories exist
for folder in [
    DATA_DIR,
    MASTER_DIR,
    TRANSACTIONS_DIR,
    REFERENCE_DIR,
    EVENTS_DIR,
    GROUND_TRUTH_DIR,
    OUTPUTS_DIR,
    ROOT_OUTPUTS_DIR,
    DATABASE_DIR,
    SQL_DIR,
    DOCS_DIR,
]:
    folder.mkdir(parents=True, exist_ok=True)
