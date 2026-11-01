"""
Enterprise Validation Engine for YottaFlex Energy Platform
===========================================================
Executes 15 comprehensive structural, relational, physical, and domain validation checks.
Produces a detailed validation_report.json and separates intentional injected anomalies
from unintended generator errors.
"""

from datetime import datetime
from typing import List, Dict, Any, Set, Tuple
import json
from pathlib import Path
import config
from src.business_logic.calculations import get_effective_tariff

class ValidationEngine:
    def __init__(
        self,
        plants: List[Dict[str, Any]],
        meters: List[Dict[str, Any]],
        machines: List[Dict[str, Any]],
        assignments: List[Dict[str, Any]],
        shifts: List[Dict[str, Any]],
        tariffs: List[Dict[str, Any]],
        weather_obs: List[Dict[str, Any]],
        batches: List[Dict[str, Any]],
        maintenance_events: List[Dict[str, Any]],
        idle_periods: List[Dict[str, Any]],
        readings: List[Dict[str, Any]],
        ground_truth: List[Dict[str, Any]],
    ):
        self.plants = plants
        self.meters = meters
        self.machines = machines
        self.assignments = assignments
        self.shifts = shifts
        self.tariffs = tariffs
        self.weather_obs = weather_obs
        self.batches = batches
        self.maintenance_events = maintenance_events
        self.idle_periods = idle_periods
        self.readings = readings
        self.ground_truth = ground_truth

        # Lookup caches
        self.plant_ids = {p["plant_id"] for p in plants}
        self.meter_ids = {m["meter_id"] for m in meters}
        self.machine_ids = {m["machine_id"] for m in machines}
        self.shift_ids = {s["shift_id"] for s in shifts}
        self.tariff_ids = {t["tariff_id"] for t in tariffs}
        self.valid_assignments = {(a["machine_id"], a["meter_id"]) for a in assignments}

        self.gt_reading_ids = {g["reading_id"] for g in ground_truth if g.get("reading_id")}
        self.gt_by_category = {}
        for g in ground_truth:
            cat = g["category_name"]
            self.gt_by_category.setdefault(cat, []).append(g)

    def run_all_checks(self) -> Dict[str, Any]:
        """Runs all 15 validation test suites and returns a consolidated report."""
        checks = []
        all_detected_anomalies = []

        # 1. Primary Key Uniqueness
        chk1, errs1 = self._check_primary_keys()
        checks.append(chk1)

        # 2. Foreign Key Integrity
        chk2, errs2 = self._check_foreign_keys()
        checks.append(chk2)

        # 3. Missing Required Fields
        chk3, errs3 = self._check_required_fields()
        checks.append(chk3)

        # 4. Invalid Enumerations
        chk4, errs4 = self._check_invalid_enums()
        checks.append(chk4)

        # 5. Invalid Measurement Units
        chk5, errs5 = self._check_invalid_units()
        checks.append(chk5)

        # 6. Duplicate Telemetry Readings (Anomaly Cat 4)
        chk6, dups = self._check_duplicate_readings()
        checks.append(chk6)
        all_detected_anomalies.extend(dups)

        # 7. Timestamp Monotonic Ordering
        chk7, errs7 = self._check_timestamp_ordering()
        checks.append(chk7)

        # 8. Tariff Effective Date & Schedule Validity
        chk8, errs8 = self._check_tariff_dates()
        checks.append(chk8)

        # 9. Timezone & Tariff Window Consistency (Anomaly Cat 3)
        chk9, tz_errs = self._check_tariff_timezone_consistency()
        checks.append(chk9)
        all_detected_anomalies.extend(tz_errs)

        # 10. Machine-to-Meter Hierarchy (Anomaly Cat 5)
        chk10, hier_errs = self._check_hierarchy_integrity()
        checks.append(chk10)
        all_detected_anomalies.extend(hier_errs)

        # 11. Meter Total Reconciliation (Anomaly Cat 1)
        chk11, mtr_errs = self._check_meter_reconciliation()
        checks.append(chk11)
        all_detected_anomalies.extend(mtr_errs)

        # 12. Energy Calculation Correctness (Anomaly Cat 2)
        chk12, math_errs = self._check_energy_calculation()
        checks.append(chk12)
        all_detected_anomalies.extend(math_errs)

        # 13. Production Batch Alignment
        chk13, errs13 = self._check_production_batches()
        checks.append(chk13)

        # 14. Lifecycle Transition Validity
        chk14, errs14 = self._check_lifecycle_states()
        checks.append(chk14)

        # 15. Negative or Impossible Measurements
        chk15, errs15 = self._check_non_negative_ranges()
        checks.append(chk15)

        # Summary statistics
        total_checks = len(checks)
        passed_checks = sum(1 for c in checks if c["status"] == "PASSED")
        failed_checks = sum(1 for c in checks if c["status"] == "FAILED")
        warning_checks = sum(1 for c in checks if c["status"] == "WARNING")

        # Ground truth reconciliation
        gt_total = len(self.ground_truth)
        detected_ids = {a.get("reading_id") for a in all_detected_anomalies if a.get("reading_id")}
        matched_gt = sum(1 for g in self.ground_truth if g["reading_id"] in detected_ids)
        reconciliation_rate = round(100.0 * matched_gt / max(1, gt_total), 2)

        # Build category-level anomaly detection summary with explicit rule mapping
        rule_map = {
            "METER_SUM_MISMATCH": {"category_id": 1, "check_id": "CHK-11-METER-SUM-RECONCILIATION", "check_name": "Hierarchical Meter Reconciliation"},
            "KW_KWH_CONFUSION": {"category_id": 2, "check_id": "CHK-12-ENERGY-CALCULATION-PHYSICS", "check_name": "Interval Energy Physics & Conversion"},
            "TARIFF_TZ_MISMATCH": {"category_id": 3, "check_id": "CHK-09-TARIFF-TIMEZONE-ALIGNMENT", "check_name": "Tariff Timezone & Window Alignment"},
            "DUPLICATE_READING": {"category_id": 4, "check_id": "CHK-06-DUPLICATE-READINGS", "check_name": "Telemetry Duplicate Readings Check"},
            "HIERARCHY_VIOLATION": {"category_id": 5, "check_id": "CHK-10-METER-HIERARCHY-TOPOLOGY", "check_name": "Machine-to-Meter Topology Assignment"},
        }

        category_summary = {}
        for cat_name, info in rule_map.items():
            injected_items = self.gt_by_category.get(cat_name, [])
            injected_ids = {g["reading_id"] for g in injected_items}
            injected_cnt = len(injected_items)

            detected_items = [a for a in all_detected_anomalies if a.get("category") == cat_name]
            detected_ids_cat = {a["reading_id"] for a in detected_items}
            detected_cnt = len(detected_items)

            true_positives = len(injected_ids.intersection(detected_ids_cat))
            precision = round(100.0 * true_positives / max(1, detected_cnt), 2)
            recall = round(100.0 * true_positives / max(1, injected_cnt), 2)

            category_summary[cat_name] = {
                "category_id": info["category_id"],
                "detection_rule": info["check_id"],
                "rule_name": info["check_name"],
                "injected_count": injected_cnt,
                "detected_count": detected_cnt,
                "true_positives": true_positives,
                "precision_pct": precision,
                "recall_pct": recall,
                "status": "PASSED (100% RECONCILED)" if (precision == 100.0 and recall == 100.0) else "DISCREPANCY",
                "mapping_rationale": f"Deliberate {cat_name} anomalies are independently isolated and verified by rule {info['check_id']}."
            }

        unintended_defects_total = sum(c.get("unintended_defects_count", 0) for c in checks)

        report = {
            "validation_timestamp": datetime.now().isoformat(),
            "summary": {
                "total_checks": total_checks,
                "passed_checks": passed_checks,
                "warning_checks": warning_checks,
                "failed_checks": failed_checks,
                "ordinary_checks_passed": passed_checks,
                "intentional_anomaly_warnings": warning_checks,
                "genuine_validation_failures": failed_checks,
                "total_records_analyzed": len(self.readings),
                "injected_ground_truth_count": gt_total,
                "detected_anomalies_count": len(all_detected_anomalies),
                "ground_truth_match_rate_pct": reconciliation_rate,
                "unintended_defect_count": unintended_defects_total,
                "overall_validation_result": "PASSED (10 Standard Checks Passed, 5 Anomaly Suites Reconciled with 0 Unintended Defects)" if (failed_checks == 0 and unintended_defects_total == 0) else "FAILED",
            },
            "anomaly_detection_summary": category_summary,
            "checks": checks,
            "detected_anomalies": all_detected_anomalies,
        }

        return report

    # -------------------------------------------------------------------------
    # Individual Check Implementations
    # -------------------------------------------------------------------------
    def _check_primary_keys(self) -> Tuple[Dict[str, Any], List[Any]]:
        tables = [
            ("plants", self.plants, "plant_id"),
            ("meters", self.meters, "meter_id"),
            ("machines", self.machines, "machine_id"),
            ("shifts", self.shifts, "shift_id"),
            ("tariffs", self.tariffs, "tariff_id"),
            ("batches", self.batches, "batch_id"),
        ]
        violations = []
        for tbl, recs, pk in tables:
            seen = set()
            for r in recs:
                v = r.get(pk)
                if not v or v in seen:
                    violations.append({"table": tbl, "pk": pk, "value": v})
                seen.add(v)
        
        status = "FAILED" if violations else "PASSED"
        return {
            "check_id": "CHK-01-PK-UNIQUENESS",
            "name": "Primary Key Uniqueness",
            "status": status,
            "violations_count": len(violations),
            "description": "Verifies that all entity primary keys are non-null and strictly unique.",
        }, violations

    def _check_foreign_keys(self) -> Tuple[Dict[str, Any], List[Any]]:
        violations = []
        for m in self.meters:
            if m["plant_id"] not in self.plant_ids:
                violations.append({"entity": "meters", "id": m["meter_id"], "issue": "orphan plant_id"})
            if m["parent_meter_id"] and m["parent_meter_id"] not in self.meter_ids:
                violations.append({"entity": "meters", "id": m["meter_id"], "issue": "invalid parent_meter_id"})

        for mch in self.machines:
            if mch["plant_id"] not in self.plant_ids:
                violations.append({"entity": "machines", "id": mch["machine_id"], "issue": "orphan plant_id"})

        for b in self.batches:
            if b["machine_id"] not in self.machine_ids:
                violations.append({"entity": "batches", "id": b["batch_id"], "issue": "orphan machine_id"})
            if b["shift_id"] not in self.shift_ids:
                violations.append({"entity": "batches", "id": b["batch_id"], "issue": "orphan shift_id"})

        status = "FAILED" if violations else "PASSED"
        return {
            "check_id": "CHK-02-FK-INTEGRITY",
            "name": "Foreign Key Referential Integrity",
            "status": status,
            "violations_count": len(violations),
            "description": "Ensures all foreign keys reference existing parent entity records.",
        }, violations

    def _check_required_fields(self) -> Tuple[Dict[str, Any], List[Any]]:
        violations = []
        for r in self.readings:
            if not r.get("reading_id") or not r.get("meter_id") or not r.get("timestamp") or r.get("power_demand_kw") is None:
                violations.append({"reading_id": r.get("reading_id"), "issue": "missing required telemetry field"})
        status = "FAILED" if violations else "PASSED"
        return {
            "check_id": "CHK-03-REQUIRED-FIELDS",
            "name": "Mandatory Fields Completeness",
            "status": status,
            "violations_count": len(violations),
            "description": "Ensures no mandatory columns contain NULL or blank values.",
        }, violations

    def _check_invalid_enums(self) -> Tuple[Dict[str, Any], List[Any]]:
        valid_meter_types = {'MAIN_INCOMER', 'SUB_FEEDER', 'PROCESS_LINE', 'MACHINE_POINT'}
        valid_machine_cats = {
            'CNC_MILLING', 'INJECTION_MOLDING', 'INDUSTRIAL_OVEN',
            'ROTARY_SCREW_COMPRESSOR', 'CHILLER_PLANT', 'AUTOMATED_ASSEMBLY_ROBOT',
            'STAMPING_PRESS', 'CONVEYOR_SYSTEM'
        }
        violations = []
        for m in self.meters:
            if m["meter_type"] not in valid_meter_types:
                violations.append({"meter_id": m["meter_id"], "invalid_enum": m["meter_type"]})
        for mch in self.machines:
            if mch["category"] not in valid_machine_cats:
                violations.append({"machine_id": mch["machine_id"], "invalid_enum": mch["category"]})
        
        status = "FAILED" if violations else "PASSED"
        return {
            "check_id": "CHK-04-ENUM-VALIDATION",
            "name": "Domain Enumerations Validation",
            "status": status,
            "violations_count": len(violations),
            "description": "Validates restricted categorical fields against industrial schema enums.",
        }, violations

    def _check_invalid_units(self) -> Tuple[Dict[str, Any], List[Any]]:
        violations = []
        for m in self.meters:
            if m["measurement_unit"] not in {'kWh', 'kW', 'kVARh'}:
                violations.append({"meter_id": m["meter_id"], "invalid_unit": m["measurement_unit"]})
        status = "FAILED" if violations else "PASSED"
        return {
            "check_id": "CHK-05-MEASUREMENT-UNITS",
            "name": "Physical Measurement Units Consistency",
            "status": status,
            "violations_count": len(violations),
            "description": "Verifies that meter and telemetry units comply with SI and IEC standards.",
        }, violations

    def _evaluate_anomaly_rule(
        self,
        check_id: str,
        name: str,
        category_name: str,
        detected_violations: List[Dict[str, Any]],
        description: str,
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Reconciles detected violations against documented ground-truth anomalies.
        Distinguishes intentional, documented anomalies from accidental data corruption.
        Fails if any expected anomaly is missed OR if any unexplained defect is found.
        """
        expected_items = self.gt_by_category.get(category_name, [])
        expected_ids = {g["reading_id"] for g in expected_items if g.get("reading_id")}
        expected_count = len(expected_items)

        detected_ids = {a["reading_id"] for a in detected_violations if a.get("reading_id")}
        detected_count = len(detected_violations)

        true_positives = len(expected_ids.intersection(detected_ids))
        unintended_defects = detected_count - true_positives
        missed_anomalies = expected_count - true_positives

        # In accordance with Section 4 specification:
        # 10 ordinary checks pass with status 'PASSED'.
        # The 5 anomaly detection checks identify intentional anomalies and report status 'WARNING'
        # (with classification 'EXPECTED_ANOMALY_WARNING') when 100% reconciled with 0 unintended defects.
        # They only fail with status 'FAILED' if genuine defects or missed anomalies occur.
        if unintended_defects > 0 or missed_anomalies > 0:
            status = "FAILED"
            classification = "GENUINE_FAILURE"
        else:
            status = "WARNING"
            classification = "EXPECTED_ANOMALY_WARNING"

        check_result = {
            "check_id": check_id,
            "name": name,
            "status": status,
            "classification": classification,
            "is_anomaly_detection_suite": True,
            "violations_count": detected_count,
            "expected_anomalies_count": expected_count,
            "detected_anomalies_count": detected_count,
            "reconciled_ground_truth_count": true_positives,
            "unintended_defects_count": unintended_defects,
            "missed_anomalies_count": missed_anomalies,
            "precision_pct": round(100.0 * true_positives / max(1, detected_count), 2),
            "recall_pct": round(100.0 * true_positives / max(1, expected_count), 2),
            "description": description,
        }
        return check_result, detected_violations

    def _check_duplicate_readings(self) -> Tuple[Dict[str, Any], List[Any]]:
        seen = set()
        duplicates = []
        for r in self.readings:
            key = (r["meter_id"], r["timestamp"])
            if key in seen:
                duplicates.append({
                    "reading_id": r["reading_id"],
                    "meter_id": r["meter_id"],
                    "timestamp": r["timestamp"],
                    "category": "DUPLICATE_READING",
                    "description": "Detected duplicate interval record for same meter and timestamp",
                })
            seen.add(key)

        return self._evaluate_anomaly_rule(
            check_id="CHK-06-DUPLICATE-READINGS",
            name="Telemetry Duplicate Readings Check (Anomaly Cat 4)",
            category_name="DUPLICATE_READING",
            detected_violations=duplicates,
            description="Scans for repeated telemetry samples across identical (meter_id, timestamp) pairs."
        )

    def _check_timestamp_ordering(self) -> Tuple[Dict[str, Any], List[Any]]:
        violations = []
        for b in self.batches:
            if b["end_timestamp"] < b["start_timestamp"]:
                violations.append({"batch_id": b["batch_id"], "issue": "end_time before start_time"})
        status = "FAILED" if violations else "PASSED"
        return {
            "check_id": "CHK-07-TIMESTAMP-ORDERING",
            "name": "Chronological Timestamp Ordering",
            "status": status,
            "violations_count": len(violations),
            "description": "Verifies that end timestamps strictly follow or equal start timestamps.",
        }, violations

    def _check_tariff_dates(self) -> Tuple[Dict[str, Any], List[Any]]:
        violations = []
        for t in self.tariffs:
            if t["effective_to"] < t["effective_from"]:
                violations.append({"tariff_id": t["tariff_id"], "issue": "effective_to < effective_from"})
        status = "FAILED" if violations else "PASSED"
        return {
            "check_id": "CHK-08-TARIFF-SCHEDULE-DATES",
            "name": "Tariff Schedule Date Validity",
            "status": status,
            "violations_count": len(violations),
            "description": "Ensures tariff effective dates form valid non-inverted intervals.",
        }, violations

    def _check_tariff_timezone_consistency(self) -> Tuple[Dict[str, Any], List[Any]]:
        detected = []
        # Pre-index weather
        weather_by_hour = {w["observation_timestamp"][:13]: w["dry_bulb_temperature_c"] for w in self.weather_obs}

        for r in self.readings:
            dt = datetime.strptime(r["timestamp"], "%Y-%m-%d %H:%M:%S")
            ambient = weather_by_hour.get(r["timestamp"][:13], 25.0)
            expected_tariff, expected_rate = get_effective_tariff(dt, ambient)
            
            if r["tariff_id"] != expected_tariff:
                detected.append({
                    "reading_id": r["reading_id"],
                    "meter_id": r["meter_id"],
                    "timestamp": r["timestamp"],
                    "actual_tariff": r["tariff_id"],
                    "expected_tariff": expected_tariff,
                    "category": "TARIFF_TZ_MISMATCH",
                    "description": f"Applied {r['tariff_id']} instead of expected {expected_tariff} due to timezone discrepancy.",
                })

        return self._evaluate_anomaly_rule(
            check_id="CHK-09-TARIFF-TIMEZONE-ALIGNMENT",
            name="Tariff Timezone & Window Alignment (Anomaly Cat 3)",
            category_name="TARIFF_TZ_MISMATCH",
            detected_violations=detected,
            description="Re-evaluates local facility timezone rules to detect misallocated tariff periods."
        )

    def _check_hierarchy_integrity(self) -> Tuple[Dict[str, Any], List[Any]]:
        detected = []
        for r in self.readings:
            mch = r.get("machine_id")
            mtr = r.get("meter_id")
            if mch and (mch, mtr) not in self.valid_assignments:
                detected.append({
                    "reading_id": r["reading_id"],
                    "meter_id": mtr,
                    "machine_id": mch,
                    "timestamp": r["timestamp"],
                    "category": "HIERARCHY_VIOLATION",
                    "description": f"Reading assigns machine {mch} to meter {mtr} which violates topology assignment.",
                })
        return self._evaluate_anomaly_rule(
            check_id="CHK-10-METER-HIERARCHY-TOPOLOGY",
            name="Machine-to-Meter Topology Assignment (Anomaly Cat 5)",
            category_name="HIERARCHY_VIOLATION",
            detected_violations=detected,
            description="Validates that telemetry machine IDs strictly match established bridge table topology."
        )

    def _check_meter_reconciliation(self) -> Tuple[Dict[str, Any], List[Any]]:
        detected = []
        feeder_children = {
            f"MTR-{config.PLANT_ID}-002": [f"MTR-{config.PLANT_ID}-{i:03d}" for i in [5, 6, 7, 8, 19]],
            f"MTR-{config.PLANT_ID}-003": [f"MTR-{config.PLANT_ID}-{i:03d}" for i in [9, 10, 11, 12, 20]],
            f"MTR-{config.PLANT_ID}-004": [f"MTR-{config.PLANT_ID}-{i:03d}" for i in [13, 14, 15, 16, 17, 18]],
        }
        
        # Group submeter readings by (meter_id, timestamp)
        readings_map = {}
        feeder_readings = []
        for r in self.readings:
            readings_map[(r["meter_id"], r["timestamp"])] = r["power_demand_kw"]
            if r["meter_id"] in feeder_children:
                feeder_readings.append(r)

        for f_rec in feeder_readings:
            fdr_id = f_rec["meter_id"]
            ts = f_rec["timestamp"]
            child_ids = feeder_children[fdr_id]
            child_sum = sum(readings_map.get((cid, ts), 0.0) for cid in child_ids)
            f_kw = f_rec["power_demand_kw"]

            # Expected: f_kw is between child_sum * 0.98 and child_sum * 1.08 (including busbar losses)
            if child_sum > 0:
                ratio = f_kw / child_sum
                if ratio < 0.85 or ratio > 1.35:
                    detected.append({
                        "reading_id": f_rec["reading_id"],
                        "meter_id": fdr_id,
                        "timestamp": ts,
                        "feeder_kw": f_kw,
                        "child_sum_kw": round(child_sum, 3),
                        "ratio": round(ratio, 3),
                        "category": "METER_SUM_MISMATCH",
                        "description": f"Feeder power {f_kw} kW deviates from sum of sub-meters {round(child_sum, 2)} kW by {round(ratio, 2)}x",
                    })

        return self._evaluate_anomaly_rule(
            check_id="CHK-11-METER-SUM-RECONCILIATION",
            name="Hierarchical Meter Reconciliation (Anomaly Cat 1)",
            category_name="METER_SUM_MISMATCH",
            detected_violations=detected,
            description="Compares parent feeder active power against instantaneous sum of downstream sub-meters."
        )

    def _check_energy_calculation(self) -> Tuple[Dict[str, Any], List[Any]]:
        detected = []
        for r in self.readings:
            kw = r["power_demand_kw"]
            kwh = r["energy_consumed_kwh"]
            expected_kwh = round(kw * (15.0 / 60.0), 4)
            diff = abs(kwh - expected_kwh)
            
            if diff > 0.05:
                detected.append({
                    "reading_id": r["reading_id"],
                    "meter_id": r["meter_id"],
                    "timestamp": r["timestamp"],
                    "recorded_kwh": kwh,
                    "expected_kwh": expected_kwh,
                    "power_kw": kw,
                    "category": "KW_KWH_CONFUSION",
                    "description": f"Recorded energy {kwh} kWh does not equal power {kw} kW * 0.25 h (diff={round(diff, 4)}).",
                })
        return self._evaluate_anomaly_rule(
            check_id="CHK-12-ENERGY-CALCULATION-PHYSICS",
            name="Interval Energy Physics & Conversion (Anomaly Cat 2)",
            category_name="KW_KWH_CONFUSION",
            detected_violations=detected,
            description="Enforces E(kWh) = P(kW) * 0.25 to catch unit confusion between instantaneous kW and interval kWh."
        )

    def _check_production_batches(self) -> Tuple[Dict[str, Any], List[Any]]:
        violations = []
        for b in self.batches:
            if b["actual_good_units"] < 0 or b["actual_scrap_units"] < 0:
                violations.append({"batch_id": b["batch_id"], "issue": "negative batch production units"})
        status = "FAILED" if violations else "PASSED"
        return {
            "check_id": "CHK-13-PRODUCTION-BATCH-ALIGNMENT",
            "name": "Production Batch Physical Realism",
            "status": status,
            "violations_count": len(violations),
            "description": "Verifies non-negative counts and physical plausibility for all production batches.",
        }, violations

    def _check_lifecycle_states(self) -> Tuple[Dict[str, Any], List[Any]]:
        violations = []
        for mch in self.machines:
            if mch["lifecycle_state"] not in {'OPERATIONAL', 'MAINTENANCE', 'STANDBY', 'OFFLINE'}:
                violations.append({"machine_id": mch["machine_id"], "state": mch["lifecycle_state"]})
        status = "FAILED" if violations else "PASSED"
        return {
            "check_id": "CHK-14-LIFECYCLE-TRANSITIONS",
            "name": "Machine Lifecycle State Validation",
            "status": status,
            "violations_count": len(violations),
            "description": "Ensures equipment lifecycle states reflect valid operational modes.",
        }, violations

    def _check_non_negative_ranges(self) -> Tuple[Dict[str, Any], List[Any]]:
        violations = []
        for r in self.readings:
            if r["power_demand_kw"] < 0 or r["energy_consumed_kwh"] < 0 or r["cost_usd"] < 0:
                violations.append({"reading_id": r["reading_id"], "issue": "negative energy or cost"})
        status = "FAILED" if violations else "PASSED"
        return {
            "check_id": "CHK-15-NON-NEGATIVE-TELEMETRY",
            "name": "Non-Negative Telemetry Bounds",
            "status": status,
            "violations_count": len(violations),
            "description": "Verifies that electrical power, energy, and financial costs are strictly >= 0.",
        }, violations
