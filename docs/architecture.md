# Architecture Overview & Engineering Blueprint
## YottaFlex Industrial Energy Analytics Platform

```
+-------------------------------------------------------------------------------------------------+
|                                     DATA GENERATION ENGINE                                      |
|  - Deterministic Seed: 20261022                                                                 |
|  - Master Generator (Plant, 20 Meters, 16 Machines, Bridge Mappings)                            |
|  - Reference Generator (Shifts, Tariffs, Weather Observations)                                  |
|  - Transaction Generator (2,000 Production Batches, 172,800 Baseline 15-min Telemetry Readings) |
+-------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+-------------------------------------------------------------------------------------------------+
|                                   ANOMALY INJECTION FRAMEWORK                                   |
|  - Cat 1: Meter sum vs interval discrepancy (Sub-meter reconciliation error)                    |
|  - Cat 2: kW confused with kWh (Power rate vs 15-min energy conversion error)                   |
|  - Cat 3: Tariff timezone mismatch (Shifted timestamps & misallocated peak tariffs)             |
|  - Cat 4: Duplicate energy readings (Telemetry retry duplication)                               |
|  - Cat 5: Energy assigned outside meter hierarchy (Unlinked asset telemetry)                    |
|  - Ground Truth Registry (ground_truth.csv / json)                                              |
+-------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+-------------------------------------------------------------------------------------------------+
|                                 ENTERPRISE VALIDATION ENGINE                                    |
|  - 15 Validation Check Suites: PK, FK, Enum, Nulls, Timestamps, Hierarchy, Range, Units         |
|  - Reconciles Injected vs Detected anomalies                                                    |
|  - Emits validation_report.json                                                                 |
+-------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+-------------------------------------------------------------------------------------------------+
|                              ANALYTICS & RELATIONAL PERSISTENCE                                 |
|  - SQLite 3 Relational Database (energy_analytics.db) with Foreign Keys & B-Tree Indexes        |
|  - Export: data/master, transactions, reference, events, outputs CSVs                           |
|  - 10 Specialized SQL Analytical Queries (CTEs, Window Functions, Group By)                     |
|  - Recommendations Engine (Quantified ROI, kWh and USD savings)                                 |
+-------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+-------------------------------------------------------------------------------------------------+
|                             INTERACTIVE ANALYTICS APPLICATION                                   |
|  - Full-stack Dashboard UI with Live SQL Query Studio                                           |
|  - Real-time KPI Dashboards, Anomaly Ground Truth Inspector, & Validation Metrics               |
|  - Automated Pytest Suite for continuous validation                                             |
+-------------------------------------------------------------------------------------------------+
```

### Determinism & Reproducibility Guarantees
- The random number generation uses a fixed seed (`20261022`).
- Pseudorandom streams are partitioned deterministically per entity type.
- Timestamp sequences are monotonically incremented using 15-minute ISO 8601 UTC offsets (`timedelta(minutes=15)`).
- SHA-256 file checksums are calculated and verified to ensure zero-drift reproducibility across successive pipeline executions.
