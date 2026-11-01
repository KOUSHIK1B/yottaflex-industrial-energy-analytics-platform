-- ============================================================================
-- YottaFlex Industrial Energy Analytics Platform - Relational Schema
-- Database: SQLite 3 / Standard ANSI SQL compliant
-- Deterministic primary keys, strict foreign keys, check constraints & indices
-- ============================================================================

PRAGMA foreign_keys = ON;

-- ----------------------------------------------------------------------------
-- 1. PLANTS (Manufacturing facilities)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS plants (
    plant_id VARCHAR(32) PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    industry_type VARCHAR(64) NOT NULL,
    country VARCHAR(3) NOT NULL DEFAULT 'USA',
    state VARCHAR(32) NOT NULL,
    city VARCHAR(64) NOT NULL,
    timezone VARCHAR(64) NOT NULL DEFAULT 'America/Chicago',
    grid_connection_voltage_kv NUMERIC(6,2) NOT NULL CHECK (grid_connection_voltage_kv > 0),
    contracted_peak_capacity_kw NUMERIC(10,2) NOT NULL CHECK (contracted_peak_capacity_kw > 0),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 2. METERS (Utility boundary & sub-meters)
-- ID Convention: MTR-<plant-id>-<001..999>
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS meters (
    meter_id VARCHAR(64) PRIMARY KEY,
    plant_id VARCHAR(32) NOT NULL,
    parent_meter_id VARCHAR(64),
    name VARCHAR(128) NOT NULL,
    meter_type VARCHAR(32) NOT NULL CHECK (meter_type IN ('MAIN_INCOMER', 'SUB_FEEDER', 'PROCESS_LINE', 'MACHINE_POINT')),
    measurement_unit VARCHAR(16) NOT NULL CHECK (measurement_unit IN ('kWh', 'kW', 'kVARh')),
    voltage_rating_v NUMERIC(8,2) NOT NULL CHECK (voltage_rating_v > 0),
    current_rating_a NUMERIC(8,2) NOT NULL CHECK (current_rating_a > 0),
    installation_date DATE NOT NULL,
    status VARCHAR(16) NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'MAINTENANCE', 'DECOMMISSIONED')),
    FOREIGN KEY (plant_id) REFERENCES plants(plant_id) ON DELETE RESTRICT,
    FOREIGN KEY (parent_meter_id) REFERENCES meters(meter_id) ON DELETE RESTRICT
);

-- ----------------------------------------------------------------------------
-- 3. MACHINES (Production assets)
-- ID Convention: MCH-<plant-id>-<001..999>
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS machines (
    machine_id VARCHAR(64) PRIMARY KEY,
    plant_id VARCHAR(32) NOT NULL,
    name VARCHAR(128) NOT NULL,
    category VARCHAR(64) NOT NULL CHECK (category IN (
        'CNC_MILLING', 'INJECTION_MOLDING', 'INDUSTRIAL_OVEN',
        'ROTARY_SCREW_COMPRESSOR', 'CHILLER_PLANT', 'AUTOMATED_ASSEMBLY_ROBOT',
        'STAMPING_PRESS', 'CONVEYOR_SYSTEM'
    )),
    rated_power_kw NUMERIC(8,2) NOT NULL CHECK (rated_power_kw > 0),
    standby_power_kw NUMERIC(8,2) NOT NULL CHECK (standby_power_kw >= 0),
    operating_power_kw NUMERIC(8,2) NOT NULL CHECK (operating_power_kw >= standby_power_kw),
    commissioning_date DATE NOT NULL,
    lifecycle_state VARCHAR(24) NOT NULL DEFAULT 'OPERATIONAL' CHECK (lifecycle_state IN ('OPERATIONAL', 'MAINTENANCE', 'STANDBY', 'OFFLINE')),
    FOREIGN KEY (plant_id) REFERENCES plants(plant_id) ON DELETE RESTRICT
);

-- ----------------------------------------------------------------------------
-- 4. MACHINE METER ASSIGNMENTS (Bridge Table with historical effective dates)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS machine_meter_assignments (
    assignment_id VARCHAR(64) PRIMARY KEY,
    machine_id VARCHAR(64) NOT NULL,
    meter_id VARCHAR(64) NOT NULL,
    effective_from TIMESTAMP NOT NULL,
    effective_to TIMESTAMP,
    allocation_percentage NUMERIC(5,2) NOT NULL DEFAULT 100.00 CHECK (allocation_percentage > 0 AND allocation_percentage <= 100.00),
    is_primary_meter BOOLEAN NOT NULL DEFAULT 1,
    FOREIGN KEY (machine_id) REFERENCES machines(machine_id) ON DELETE RESTRICT,
    FOREIGN KEY (meter_id) REFERENCES meters(meter_id) ON DELETE RESTRICT,
    CONSTRAINT chk_dates CHECK (effective_to IS NULL OR effective_to >= effective_from)
);

-- ----------------------------------------------------------------------------
-- 5. SHIFTS (Operating shifts)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS shifts (
    shift_id VARCHAR(32) PRIMARY KEY,
    plant_id VARCHAR(32) NOT NULL,
    name VARCHAR(64) NOT NULL,
    start_time_local TIME NOT NULL,
    end_time_local TIME NOT NULL,
    duration_hours NUMERIC(4,2) NOT NULL CHECK (duration_hours > 0),
    standard_manning_level INTEGER NOT NULL CHECK (standard_manning_level > 0),
    shift_multiplier NUMERIC(4,2) NOT NULL DEFAULT 1.00,
    FOREIGN KEY (plant_id) REFERENCES plants(plant_id) ON DELETE RESTRICT
);

-- ----------------------------------------------------------------------------
-- 6. TARIFFS (Time-of-Use electricity tariffs)
-- ID Convention: TAR-2026-<001..999>
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tariffs (
    tariff_id VARCHAR(64) PRIMARY KEY,
    plant_id VARCHAR(32) NOT NULL,
    tariff_code VARCHAR(32) NOT NULL,
    name VARCHAR(128) NOT NULL,
    period_type VARCHAR(24) NOT NULL CHECK (period_type IN ('OFF_PEAK', 'SHOULDER', 'ON_PEAK', 'CRITICAL_PEAK')),
    rate_per_kwh_usd NUMERIC(8,4) NOT NULL CHECK (rate_per_kwh_usd >= 0),
    demand_charge_per_kw_usd NUMERIC(8,4) NOT NULL DEFAULT 0.0 CHECK (demand_charge_per_kw_usd >= 0),
    start_hour INTEGER NOT NULL CHECK (start_hour >= 0 AND start_hour < 24),
    end_hour INTEGER NOT NULL CHECK (end_hour >= 0 AND end_hour < 24),
    is_weekend_applicable BOOLEAN NOT NULL DEFAULT 0,
    effective_from DATE NOT NULL,
    effective_to DATE NOT NULL,
    FOREIGN KEY (plant_id) REFERENCES plants(plant_id) ON DELETE RESTRICT,
    CONSTRAINT chk_tariff_dates CHECK (effective_to >= effective_from)
);

-- ----------------------------------------------------------------------------
-- 7. WEATHER OBSERVATIONS (Ambient temperature, humidity & cooling load factor)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS weather_observations (
    weather_id VARCHAR(64) PRIMARY KEY,
    plant_id VARCHAR(32) NOT NULL,
    observation_timestamp TIMESTAMP NOT NULL,
    dry_bulb_temperature_c NUMERIC(5,2) NOT NULL,
    relative_humidity_pct NUMERIC(5,2) NOT NULL CHECK (relative_humidity_pct >= 0 AND relative_humidity_pct <= 100),
    solar_ghi_w_per_m2 NUMERIC(7,2) NOT NULL CHECK (solar_ghi_w_per_m2 >= 0),
    cooling_degree_load_factor NUMERIC(5,3) NOT NULL CHECK (cooling_degree_load_factor >= 0),
    FOREIGN KEY (plant_id) REFERENCES plants(plant_id) ON DELETE RESTRICT,
    UNIQUE (plant_id, observation_timestamp)
);

-- ----------------------------------------------------------------------------
-- 8. PRODUCTION BATCHES (Output tracking)
-- ID Convention: BATCH-2026-<000001..999999>
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS production_batches (
    batch_id VARCHAR(64) PRIMARY KEY,
    plant_id VARCHAR(32) NOT NULL,
    machine_id VARCHAR(64) NOT NULL,
    shift_id VARCHAR(32) NOT NULL,
    product_sku VARCHAR(64) NOT NULL,
    planned_units INTEGER NOT NULL CHECK (planned_units > 0),
    actual_good_units INTEGER NOT NULL CHECK (actual_good_units >= 0),
    actual_scrap_units INTEGER NOT NULL DEFAULT 0 CHECK (actual_scrap_units >= 0),
    start_timestamp TIMESTAMP NOT NULL,
    end_timestamp TIMESTAMP NOT NULL,
    status VARCHAR(24) NOT NULL CHECK (status IN ('COMPLETED', 'IN_PROGRESS', 'ABORTED', 'PLANNED')),
    FOREIGN KEY (plant_id) REFERENCES plants(plant_id) ON DELETE RESTRICT,
    FOREIGN KEY (machine_id) REFERENCES machines(machine_id) ON DELETE RESTRICT,
    FOREIGN KEY (shift_id) REFERENCES shifts(shift_id) ON DELETE RESTRICT,
    CONSTRAINT chk_batch_time CHECK (end_timestamp >= start_timestamp)
);

-- ----------------------------------------------------------------------------
-- 9. ENERGY READINGS (15-minute telemetry intervals)
-- ID Convention: ENG-<meter-id>-<timestamp>
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS energy_readings (
    reading_id VARCHAR(128) PRIMARY KEY,
    meter_id VARCHAR(64) NOT NULL,
    machine_id VARCHAR(64),
    timestamp TIMESTAMP NOT NULL,
    interval_minutes INTEGER NOT NULL DEFAULT 15 CHECK (interval_minutes = 15),
    power_demand_kw NUMERIC(10,3) NOT NULL CHECK (power_demand_kw >= 0),
    energy_consumed_kwh NUMERIC(10,4) NOT NULL CHECK (energy_consumed_kwh >= 0),
    reactive_energy_kvarh NUMERIC(10,4) NOT NULL DEFAULT 0.0 CHECK (reactive_energy_kvarh >= 0),
    power_factor NUMERIC(4,3) NOT NULL DEFAULT 0.95 CHECK (power_factor >= 0 AND power_factor <= 1.0),
    tariff_id VARCHAR(64) NOT NULL,
    cost_usd NUMERIC(10,4) NOT NULL CHECK (cost_usd >= 0),
    is_anomaly BOOLEAN NOT NULL DEFAULT 0,
    anomaly_category VARCHAR(64),
    FOREIGN KEY (meter_id) REFERENCES meters(meter_id) ON DELETE RESTRICT,
    FOREIGN KEY (machine_id) REFERENCES machines(machine_id) ON DELETE RESTRICT,
    FOREIGN KEY (tariff_id) REFERENCES tariffs(tariff_id) ON DELETE RESTRICT
);

-- ----------------------------------------------------------------------------
-- 10. MAINTENANCE EVENTS (Breakdown and planned maintenance)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS maintenance_events (
    event_id VARCHAR(64) PRIMARY KEY,
    machine_id VARCHAR(64) NOT NULL,
    meter_id VARCHAR(64) NOT NULL,
    event_type VARCHAR(32) NOT NULL CHECK (event_type IN ('PREVENTIVE', 'EMERGENCY_CORRECTIVE', 'FILTER_CHANGEOVER', 'LUBRICATION_OVERHAUL')),
    severity VARCHAR(16) NOT NULL CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    start_timestamp TIMESTAMP NOT NULL,
    end_timestamp TIMESTAMP NOT NULL,
    downtime_minutes NUMERIC(8,2) NOT NULL CHECK (downtime_minutes >= 0),
    technician_notes TEXT,
    cost_usd NUMERIC(10,2) NOT NULL DEFAULT 0.0,
    FOREIGN KEY (machine_id) REFERENCES machines(machine_id) ON DELETE RESTRICT,
    FOREIGN KEY (meter_id) REFERENCES meters(meter_id) ON DELETE RESTRICT,
    CONSTRAINT chk_maint_time CHECK (end_timestamp >= start_timestamp)
);

-- ----------------------------------------------------------------------------
-- 11. MACHINE IDLE PERIODS (Confirmed idle/starved/standby intervals)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS machine_idle_periods (
    idle_id VARCHAR(64) PRIMARY KEY,
    machine_id VARCHAR(64) NOT NULL,
    meter_id VARCHAR(64) NOT NULL,
    idle_reason VARCHAR(32) NOT NULL CHECK (idle_reason IN ('OPERATOR_BREAK', 'STARVED_MATERIAL', 'BLOCKED_DOWNSTREAM', 'UNPLANNED_CHANGEOVER', 'OFF_SHIFT_STANDBY')),
    start_timestamp TIMESTAMP NOT NULL,
    end_timestamp TIMESTAMP NOT NULL,
    duration_minutes NUMERIC(8,2) NOT NULL CHECK (duration_minutes > 0),
    energy_wasted_kwh NUMERIC(10,4) NOT NULL CHECK (energy_wasted_kwh >= 0),
    cost_wasted_usd NUMERIC(10,4) NOT NULL CHECK (cost_wasted_usd >= 0),
    FOREIGN KEY (machine_id) REFERENCES machines(machine_id) ON DELETE RESTRICT,
    FOREIGN KEY (meter_id) REFERENCES meters(meter_id) ON DELETE RESTRICT,
    CONSTRAINT chk_idle_time CHECK (end_timestamp >= start_timestamp)
);

-- ----------------------------------------------------------------------------
-- 12. RECOMMENDATIONS (Actionable optimization opportunities)
-- ID Convention: REC-2026-<000001..999999>
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS recommendations (
    recommendation_id VARCHAR(64) PRIMARY KEY,
    machine_id VARCHAR(64) NOT NULL,
    meter_id VARCHAR(64),
    category VARCHAR(64) NOT NULL CHECK (category IN (
        'STANDBY_REDUCTION', 'PEAK_LOAD_SHAVING', 'TARIFF_LOAD_SHIFT',
        'COMPRESSED_AIR_LEAK', 'CHILLER_OPTIMIZATION', 'MAINTENANCE_TUNING',
        'THERMAL_HEAT_RECOVERY'
    )),
    title VARCHAR(128) NOT NULL,
    issue_description TEXT NOT NULL,
    supporting_evidence TEXT NOT NULL,
    baseline_annual_kwh NUMERIC(12,2) NOT NULL CHECK (baseline_annual_kwh >= 0),
    expected_savings_kwh NUMERIC(12,2) NOT NULL CHECK (expected_savings_kwh >= 0),
    estimated_annual_cost_savings_usd NUMERIC(10,2) NOT NULL CHECK (estimated_annual_cost_savings_usd >= 0),
    implementation_cost_usd NUMERIC(10,2) NOT NULL DEFAULT 0.0 CHECK (implementation_cost_usd >= 0),
    payback_months NUMERIC(5,1) NOT NULL DEFAULT 0.0,
    priority VARCHAR(16) NOT NULL CHECK (priority IN ('HIGH', 'MEDIUM', 'LOW')),
    status VARCHAR(24) NOT NULL DEFAULT 'NEW' CHECK (status IN ('NEW', 'REVIEWED', 'APPROVED', 'IN_PROGRESS', 'IMPLEMENTED', 'REJECTED')),
    modeled_savings_type VARCHAR(32) NOT NULL DEFAULT 'SYNTHETIC_ESTIMATE',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (machine_id) REFERENCES machines(machine_id) ON DELETE RESTRICT
);

-- ----------------------------------------------------------------------------
-- 13. ANOMALY GROUND TRUTH (Documented injected anomalies registry)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS anomaly_ground_truth (
    anomaly_id VARCHAR(64) PRIMARY KEY,
    category_id INTEGER NOT NULL CHECK (category_id BETWEEN 1 AND 5),
    category_name VARCHAR(64) NOT NULL,
    affected_entity_type VARCHAR(32) NOT NULL,
    affected_entity_id VARCHAR(64) NOT NULL,
    reading_id VARCHAR(128),
    timestamp TIMESTAMP,
    original_value TEXT,
    injected_value TEXT,
    severity VARCHAR(16) NOT NULL CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    expected_detection_rule VARCHAR(128) NOT NULL,
    rationale TEXT NOT NULL
);

-- ----------------------------------------------------------------------------
-- PERFORMANCE INDEXES
-- ----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_readings_meter_time ON energy_readings(meter_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_readings_machine_time ON energy_readings(machine_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_readings_tariff ON energy_readings(tariff_id);
CREATE INDEX IF NOT EXISTS idx_readings_timestamp ON energy_readings(timestamp);
CREATE INDEX IF NOT EXISTS idx_batches_machine_start ON production_batches(machine_id, start_timestamp);
CREATE INDEX IF NOT EXISTS idx_weather_time ON weather_observations(observation_timestamp);
CREATE INDEX IF NOT EXISTS idx_idle_machine_time ON machine_idle_periods(machine_id, start_timestamp);
CREATE INDEX IF NOT EXISTS idx_ground_truth_cat ON anomaly_ground_truth(category_id);
