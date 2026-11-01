# Data Dictionary & Schema Specification
## YottaFlex Industrial Energy Analytics Platform

### 1. `plants` (Master Entity)
| Column Name | Data Type | Constraints | Units / Format | Description |
|---|---|---|---|---|
| `plant_id` | VARCHAR(32) | PK, Non-null | Format: `PLT-001` | Unique plant identifier |
| `name` | VARCHAR(128) | Non-null | Text | Facility name |
| `industry_type` | VARCHAR(64) | Non-null | Text | Manufacturing sector (e.g. Precision Metals & Robotics) |
| `country` | VARCHAR(3) | Non-null | ISO 3166-1 alpha-3 | Country code (`USA`) |
| `state` | VARCHAR(32) | Non-null | Text | State/Province (`TX`) |
| `city` | VARCHAR(64) | Non-null | Text | Municipal city |
| `timezone` | VARCHAR(64) | Non-null | IANA TZ | Facility operational timezone (`America/Chicago`) |
| `grid_connection_voltage_kv` | NUMERIC(6,2) | > 0 | kV | Grid primary service entrance voltage (e.g. 13.80 kV) |
| `contracted_peak_capacity_kw`| NUMERIC(10,2)| > 0 | kW | Max utility supply threshold without penalty |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | ISO 8601 | Facility creation record timestamp |

### 2. `meters` (Master Entity)
| Column Name | Data Type | Constraints | Units / Format | Description |
|---|---|---|---|---|
| `meter_id` | VARCHAR(64) | PK, Non-null | Format: `MTR-<plant>-001` | Unique meter ID |
| `plant_id` | VARCHAR(32) | FK -> `plants.plant_id` | Text | Associated manufacturing facility |
| `parent_meter_id` | VARCHAR(64) | FK -> `meters.meter_id`, Nullable | Text | Upstream hierarchical feeder (NULL for main incomer) |
| `name` | VARCHAR(128) | Non-null | Text | Human-readable meter tag (e.g. Substation #1 Incomer) |
| `meter_type` | VARCHAR(32) | CHECK IN ('MAIN_INCOMER', 'SUB_FEEDER', 'PROCESS_LINE', 'MACHINE_POINT') | Enum | Hierarchy classification |
| `measurement_unit`| VARCHAR(16) | CHECK IN ('kWh', 'kW', 'kVARh') | Standard Unit | Primary interval measurement unit |
| `voltage_rating_v`| NUMERIC(8,2) | > 0 | Volts (V) | Nominal line voltage (e.g. 480.00 V) |
| `current_rating_a`| NUMERIC(8,2) | > 0 | Amperes (A) | Max current transformer rating (e.g. 1200.00 A) |
| `installation_date`| DATE | Non-null | YYYY-MM-DD | Commissioning date |
| `status` | VARCHAR(16) | CHECK IN ('ACTIVE', 'MAINTENANCE', 'DECOMMISSIONED') | Enum | Meter operating condition |

### 3. `machines` (Master Entity)
| Column Name | Data Type | Constraints | Units / Format | Description |
|---|---|---|---|---|
| `machine_id` | VARCHAR(64) | PK, Non-null | Format: `MCH-<plant>-001` | Unique equipment identifier |
| `plant_id` | VARCHAR(32) | FK -> `plants.plant_id` | Text | Facility identifier |
| `name` | VARCHAR(128) | Non-null | Text | Machine nomenclature and cell label |
| `category` | VARCHAR(64) | CHECK IN ('CNC_MILLING', 'INJECTION_MOLDING', 'INDUSTRIAL_OVEN', 'ROTARY_SCREW_COMPRESSOR', 'CHILLER_PLANT', 'AUTOMATED_ASSEMBLY_ROBOT', 'STAMPING_PRESS', 'CONVEYOR_SYSTEM') | Enum | Industrial functional equipment class |
| `rated_power_kw` | NUMERIC(8,2) | > 0 | kW | Nameplate maximum connected electrical load |
| `standby_power_kw`| NUMERIC(8,2)| >= 0 | kW | Baseline idle / warm standby power draw |
| `operating_power_kw`| NUMERIC(8,2)| >= standby | kW | Nominal active production power draw |
| `commissioning_date`| DATE | Non-null | YYYY-MM-DD | Installation / baseline calibration date |
| `lifecycle_state` | VARCHAR(24) | CHECK IN ('OPERATIONAL', 'MAINTENANCE', 'STANDBY', 'OFFLINE') | Enum | Operational health state |

### 4. `machine_meter_assignments` (Bridge Entity)
| Column Name | Data Type | Constraints | Units / Format | Description |
|---|---|---|---|---|
| `assignment_id` | VARCHAR(64) | PK, Non-null | Text | Unique assignment identifier |
| `machine_id` | VARCHAR(64) | FK -> `machines.machine_id` | Text | Measured asset |
| `meter_id` | VARCHAR(64) | FK -> `meters.meter_id` | Text | Associated power channel meter |
| `effective_from` | TIMESTAMP | Non-null | ISO 8601 | Assignment start timestamp |
| `effective_to` | TIMESTAMP | Nullable | ISO 8601 | Assignment termination timestamp (NULL = active) |
| `allocation_percentage`| NUMERIC(5,2)| > 0 AND <= 100 | % | Power share allocated to machine |
| `is_primary_meter` | BOOLEAN | Non-null | Boolean | Flag indicating primary revenue-grade meter |

### 5. `shifts` (Reference Entity)
| Column Name | Data Type | Constraints | Units / Format | Description |
|---|---|---|---|---|
| `shift_id` | VARCHAR(32) | PK, Non-null | Format: `SHF-001` | Shift unique identifier |
| `plant_id` | VARCHAR(32) | FK -> `plants.plant_id` | Text | Facility identifier |
| `name` | VARCHAR(64) | Non-null | Text | Shift name (Morning, Afternoon, Night) |
| `start_time_local`| TIME | Non-null | HH:MM:SS | Local starting time |
| `end_time_local` | TIME | Non-null | HH:MM:SS | Local ending time |
| `duration_hours` | NUMERIC(4,2) | > 0 | Hours | Shift duration (e.g. 8.00) |
| `standard_manning_level` | INTEGER | > 0 | Headcount | Base crew size |
| `shift_multiplier`| NUMERIC(4,2)| Non-null | Factor | Production intensity scalar |

### 6. `tariffs` (Reference Entity)
| Column Name | Data Type | Constraints | Units / Format | Description |
|---|---|---|---|---|
| `tariff_id` | VARCHAR(64) | PK, Non-null | Format: `TAR-2026-001` | Unique tariff rule code |
| `plant_id` | VARCHAR(32) | FK -> `plants.plant_id` | Text | Applicable facility |
| `tariff_code` | VARCHAR(32) | Non-null | Code | Utility billing rate code |
| `name` | VARCHAR(128) | Non-null | Text | Descriptive label |
| `period_type` | VARCHAR(24) | CHECK IN ('OFF_PEAK', 'SHOULDER', 'ON_PEAK', 'CRITICAL_PEAK') | Enum | Time-of-use pricing band |
| `rate_per_kwh_usd`| NUMERIC(8,4)| >= 0 | USD ($ / kWh) | Volumetric energy consumption price |
| `demand_charge_per_kw_usd`| NUMERIC(8,4)| >= 0 | USD ($ / kW) | Monthly coincidental peak demand charge |
| `start_hour` | INTEGER | 0 to 23 | Hour | Window starting hour (inclusive) |
| `end_hour` | INTEGER | 0 to 23 | Hour | Window ending hour (exclusive) |
| `is_weekend_applicable` | BOOLEAN | Non-null | Boolean | Applies on Saturday/Sunday |
| `effective_from` | DATE | Non-null | YYYY-MM-DD | Tariff schedule start date |
| `effective_to` | DATE | Non-null | YYYY-MM-DD | Tariff schedule expiration date |

### 7. `energy_readings` (Transaction Entity)
| Column Name | Data Type | Constraints | Units / Format | Description |
|---|---|---|---|---|
| `reading_id` | VARCHAR(128) | PK, Non-null | Format: `ENG-<meter>-<ts>` | Unique telemetry record ID |
| `meter_id` | VARCHAR(64) | FK -> `meters.meter_id` | Text | Generating telemetry meter |
| `machine_id` | VARCHAR(64) | FK -> `machines.machine_id`, Nullable | Text | Dedicated machine (for sub-meters) |
| `timestamp` | TIMESTAMP | Non-null | ISO 8601 | Reading timestamp (15-min aligned) |
| `interval_minutes`| INTEGER | CHECK = 15 | Minutes | Fixed aggregation duration |
| `power_demand_kw` | NUMERIC(10,3)| >= 0 | kW | Instantaneous active power demand |
| `energy_consumed_kwh` | NUMERIC(10,4)| >= 0 | kWh | Energy consumed = `power_demand_kw * (15/60)` |
| `reactive_energy_kvarh` | NUMERIC(10,4)| >= 0 | kVARh | Inductive / capacitive reactive energy |
| `power_factor` | NUMERIC(4,3) | 0.0 to 1.0 | Ratio | cos(phi) electrical efficiency metric |
| `tariff_id` | VARCHAR(64) | FK -> `tariffs.tariff_id` | Text | Effective tariff schedule applied |
| `cost_usd` | NUMERIC(10,4)| >= 0 | USD ($) | Energy cost = `energy_consumed_kwh * rate_per_kwh` |
| `is_anomaly` | BOOLEAN | DEFAULT 0 | Boolean | Injected or validated anomaly marker |
| `anomaly_category` | VARCHAR(64)| Nullable | Text | Category tag if anomalous |

### 8. `production_batches` (Transaction Entity)
| Column Name | Data Type | Constraints | Units / Format | Description |
|---|---|---|---|---|
| `batch_id` | VARCHAR(64) | PK, Non-null | Format: `BATCH-2026-000001` | Unique production work order |
| `plant_id` | VARCHAR(32) | FK -> `plants.plant_id` | Text | Manufacturing facility |
| `machine_id` | VARCHAR(64) | FK -> `machines.machine_id` | Text | Processing machinery |
| `shift_id` | VARCHAR(32) | FK -> `shifts.shift_id` | Text | Manufacturing shift |
| `product_sku` | VARCHAR(64) | Non-null | Text | Part / item SKU |
| `planned_units` | INTEGER | > 0 | Units | Target batch quantity |
| `actual_good_units` | INTEGER | >= 0 | Units | Successfully fabricated defect-free parts |
| `actual_scrap_units`| INTEGER | >= 0 | Units | Defective parts scrapped |
| `start_timestamp`| TIMESTAMP | Non-null | ISO 8601 | Production initiation timestamp |
| `end_timestamp` | TIMESTAMP | >= start | ISO 8601 | Batch completion timestamp |
| `status` | VARCHAR(24) | CHECK IN ('COMPLETED', 'IN_PROGRESS', 'ABORTED', 'PLANNED') | Enum | Batch execution status |
