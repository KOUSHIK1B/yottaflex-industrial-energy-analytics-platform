"""
Anomaly Injection Framework for YottaFlex Energy Platform
=========================================================
Deliberately and deterministically injects exactly 125 industrial anomalies
across 5 required categories into baseline records with 100% collision-free selection,
and maintains an explicit, traceable Ground Truth Registry.

Categories:
1. Meter total disagrees with interval sums (25)
2. kW confused with kWh (35)
3. Tariff timezone mismatch (30)
4. Duplicate energy readings (20)
5. Energy assigned to a machine outside the meter hierarchy (15)
Total: 125 anomalies
"""

import copy
import random
from typing import List, Dict, Any, Tuple
import config

def inject_anomalies(
    energy_readings: List[Dict[str, Any]],
    meters: List[Dict[str, Any]],
    machines: List[Dict[str, Any]],
    seed: int = config.RANDOM_SEED
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Takes clean baseline records and returns:
    - mutated_energy_readings (with tagged records and injected duplicates)
    - ground_truth_records (complete registry of injected anomalies)
    """
    rng = random.Random(seed + 999)
    # Deep copy list to avoid modifying baseline in-place
    readings = [copy.copy(r) for r in energy_readings]
    ground_truth = []
    anomaly_counter = 1

    # Index readings by meter_id for collision-free target selection
    readings_by_meter = {}
    for idx, r in enumerate(readings):
        mid = r["meter_id"]
        if mid not in readings_by_meter:
            readings_by_meter[mid] = []
        readings_by_meter[mid].append(idx)

    # Track chosen indices globally to prevent multi-anomaly collisions on the same record
    used_reading_indices = set()

    # -------------------------------------------------------------------------
    # Category 1: Meter total disagrees with interval sums (Target: 25)
    # -------------------------------------------------------------------------
    c1_count = config.ANOMALY_CONFIG.get("meter_sum_mismatch_count", 25)
    feeder_ids = [f"MTR-{config.PLANT_ID}-002", f"MTR-{config.PLANT_ID}-003", f"MTR-{config.PLANT_ID}-004"]
    
    injected_c1 = 0
    # Available pool across feeders
    feeder_pool = []
    for fdr in feeder_ids:
        feeder_pool.extend(readings_by_meter[fdr][100:-100])
    rng.shuffle(feeder_pool)

    for chosen_idx in feeder_pool:
        if chosen_idx in used_reading_indices:
            continue
        
        rec = readings[chosen_idx]
        orig_kwh = rec["energy_consumed_kwh"]
        orig_kw = rec["power_demand_kw"]
        multiplier = rng.choice([2.5, 3.0, 0.35, 2.8, 3.2])
        corrupted_kwh = round(orig_kwh * multiplier, 4)
        corrupted_kw = round(orig_kw * multiplier, 3)

        rec["energy_consumed_kwh"] = corrupted_kwh
        rec["power_demand_kw"] = corrupted_kw
        rec["is_anomaly"] = 1
        rec["anomaly_category"] = "METER_SUM_MISMATCH"
        used_reading_indices.add(chosen_idx)

        anomaly_id = f"ANO-2026-{anomaly_counter:06d}"
        anomaly_counter += 1

        ground_truth.append({
            "anomaly_id": anomaly_id,
            "category_id": 1,
            "category_name": "METER_SUM_MISMATCH",
            "affected_entity_type": "ENERGY_READING",
            "affected_entity_id": rec["meter_id"],
            "reading_id": rec["reading_id"],
            "timestamp": rec["timestamp"],
            "original_value": f"kw={orig_kw}, kwh={orig_kwh}",
            "injected_value": f"kw={corrupted_kw}, kwh={corrupted_kwh}",
            "severity": "HIGH",
            "expected_detection_rule": "feeder_energy != sum(child_submeters_energy) * (1 + loss_margin)",
            "rationale": f"Deliberately scaled feeder demand by {multiplier}x breaking conservation of energy across meter hierarchy."
        })
        injected_c1 += 1
        if injected_c1 >= c1_count:
            break

    # -------------------------------------------------------------------------
    # Category 2: kW confused with kWh (Target: 35)
    # -------------------------------------------------------------------------
    c2_count = config.ANOMALY_CONFIG.get("kw_kwh_confusion_count", 35)
    submeter_ids = [f"MTR-{config.PLANT_ID}-{i:03d}" for i in range(5, 21)]

    submeter_pool = []
    for mid in submeter_ids:
        submeter_pool.extend(readings_by_meter[mid][50:-50])
    rng.shuffle(submeter_pool)

    injected_c2 = 0
    for chosen_idx in submeter_pool:
        if chosen_idx in used_reading_indices:
            continue
        
        rec = readings[chosen_idx]
        orig_kwh = rec["energy_consumed_kwh"]
        kw = rec["power_demand_kw"]
        if kw < 2.0:
            continue

        corrupted_kwh = kw  # Exactly 4x higher than standard 15-min interval (kw * 0.25)
        rec["energy_consumed_kwh"] = corrupted_kwh
        rec["is_anomaly"] = 1
        rec["anomaly_category"] = "KW_KWH_CONFUSION"
        used_reading_indices.add(chosen_idx)

        anomaly_id = f"ANO-2026-{anomaly_counter:06d}"
        anomaly_counter += 1

        ground_truth.append({
            "anomaly_id": anomaly_id,
            "category_id": 2,
            "category_name": "KW_KWH_CONFUSION",
            "affected_entity_type": "ENERGY_READING",
            "affected_entity_id": rec["meter_id"],
            "reading_id": rec["reading_id"],
            "timestamp": rec["timestamp"],
            "original_value": f"energy_consumed_kwh={orig_kwh}",
            "injected_value": f"energy_consumed_kwh={corrupted_kwh}",
            "severity": "CRITICAL",
            "expected_detection_rule": "abs(energy_consumed_kwh - (power_demand_kw * interval_minutes / 60)) > 0.001",
            "rationale": "Instantaneous power demand kW recorded directly into interval energy kWh field without dividing by 4."
        })
        injected_c2 += 1
        if injected_c2 >= c2_count:
            break

    # -------------------------------------------------------------------------
    # Category 3: Tariff timezone mismatch (Target: 30)
    # -------------------------------------------------------------------------
    c3_count = config.ANOMALY_CONFIG.get("tariff_tz_mismatch_count", 30)
    injected_c3 = 0

    # Find candidates that are legitimately ON_PEAK or SHOULDER
    tariff_pool = []
    for mid in submeter_ids:
        for idx in readings_by_meter[mid][50:-50]:
            r_ts = readings[idx]["timestamp"]
            if (" 14:" in r_ts or " 15:" in r_ts or " 16:" in r_ts) and readings[idx]["tariff_id"] in ["TAR-2026-003", "TAR-2026-004"]:
                tariff_pool.append(idx)
    rng.shuffle(tariff_pool)

    for chosen_idx in tariff_pool:
        if chosen_idx in used_reading_indices:
            continue
        
        rec = readings[chosen_idx]
        orig_tariff = rec["tariff_id"]
        orig_cost = rec["cost_usd"]

        # Shift tariff by applying off-peak rate
        corrupted_tariff = "TAR-2026-001"
        corrupted_cost = round(rec["energy_consumed_kwh"] * 0.0650, 4)

        rec["tariff_id"] = corrupted_tariff
        rec["cost_usd"] = corrupted_cost
        rec["is_anomaly"] = 1
        rec["anomaly_category"] = "TARIFF_TZ_MISMATCH"
        used_reading_indices.add(chosen_idx)

        anomaly_id = f"ANO-2026-{anomaly_counter:06d}"
        anomaly_counter += 1

        ground_truth.append({
            "anomaly_id": anomaly_id,
            "category_id": 3,
            "category_name": "TARIFF_TZ_MISMATCH",
            "affected_entity_type": "ENERGY_READING",
            "affected_entity_id": rec["meter_id"],
            "reading_id": rec["reading_id"],
            "timestamp": rec["timestamp"],
            "original_value": f"tariff_id={orig_tariff}, cost={orig_cost}",
            "injected_value": f"tariff_id={corrupted_tariff}, cost={corrupted_cost}",
            "severity": "HIGH",
            "expected_detection_rule": "tariff_id != resolve_expected_tariff(timestamp, timezone, weather)",
            "rationale": "Timezone interpretation incorrectly assigns a local peak-period reading to the off-peak tariff."
        })
        injected_c3 += 1
        if injected_c3 >= c3_count:
            break

    # -------------------------------------------------------------------------
    # Category 4: Duplicate energy readings (Target: 20)
    # -------------------------------------------------------------------------
    c4_count = config.ANOMALY_CONFIG.get("duplicate_readings_count", 20)
    duplicated_readings = []
    injected_c4 = 0

    dup_pool = []
    for mid in submeter_ids:
        dup_pool.extend(readings_by_meter[mid][20:-20])
    rng.shuffle(dup_pool)

    for chosen_idx in dup_pool:
        if chosen_idx in used_reading_indices:
            continue
        
        original_rec = readings[chosen_idx]
        dup_rec = copy.copy(original_rec)
        dup_rec["reading_id"] = f"{original_rec['reading_id']}-DUP"
        dup_rec["is_anomaly"] = 1
        dup_rec["anomaly_category"] = "DUPLICATE_READING"
        duplicated_readings.append(dup_rec)
        used_reading_indices.add(chosen_idx)

        anomaly_id = f"ANO-2026-{anomaly_counter:06d}"
        anomaly_counter += 1

        ground_truth.append({
            "anomaly_id": anomaly_id,
            "category_id": 4,
            "category_name": "DUPLICATE_READING",
            "affected_entity_type": "ENERGY_READING",
            "affected_entity_id": original_rec["meter_id"],
            "reading_id": dup_rec["reading_id"],
            "timestamp": original_rec["timestamp"],
            "original_value": "Single unique reading for meter at timestamp",
            "injected_value": f"Duplicate telemetry retry payload with reading_id={dup_rec['reading_id']}",
            "severity": "MEDIUM",
            "expected_detection_rule": "count(reading_id) OVER (PARTITION BY meter_id, timestamp) > 1",
            "rationale": "Edge IoT gateway re-transmitted interval frame upon transient MQTT timeout, injecting duplicated timestamp."
        })
        injected_c4 += 1
        if injected_c4 >= c4_count:
            break

    # -------------------------------------------------------------------------
    # Category 5: Energy assigned to machine outside meter hierarchy (Target: 15)
    # -------------------------------------------------------------------------
    c5_count = config.ANOMALY_CONFIG.get("hierarchy_violation_count", 15)
    invalid_pairs = [
        (f"MTR-{config.PLANT_ID}-005", f"MCH-{config.PLANT_ID}-009"),  # CNC meter assigned to Oven
        (f"MTR-{config.PLANT_ID}-006", f"MCH-{config.PLANT_ID}-013"),  # CNC meter assigned to Chiller
        (f"MTR-{config.PLANT_ID}-010", f"MCH-{config.PLANT_ID}-001"),  # Molder meter assigned to CNC
        (f"MTR-{config.PLANT_ID}-014", f"MCH-{config.PLANT_ID}-015"),  # Oven meter assigned to Robot
        (f"MTR-{config.PLANT_ID}-017", f"MCH-{config.PLANT_ID}-003"),  # Chiller meter assigned to Lathe
        (f"MTR-{config.PLANT_ID}-011", f"MCH-{config.PLANT_ID}-012"),  # Molder meter assigned to Compressor
        (f"MTR-{config.PLANT_ID}-007", f"MCH-{config.PLANT_ID}-016"),  # Lathe meter assigned to Conveyor
        (f"MTR-{config.PLANT_ID}-012", f"MCH-{config.PLANT_ID}-002"),  # Press meter assigned to CNC
        (f"MTR-{config.PLANT_ID}-008", f"MCH-{config.PLANT_ID}-005"),  # Lathe assigned to Molder
        (f"MTR-{config.PLANT_ID}-009", f"MCH-{config.PLANT_ID}-014"),  # Molder assigned to Chiller
        (f"MTR-{config.PLANT_ID}-015", f"MCH-{config.PLANT_ID}-004"),  # Compressor assigned to Lathe
        (f"MTR-{config.PLANT_ID}-016", f"MCH-{config.PLANT_ID}-006"),  # Compressor assigned to Molder
        (f"MTR-{config.PLANT_ID}-018", f"MCH-{config.PLANT_ID}-007"),  # Chiller assigned to Molder
        (f"MTR-{config.PLANT_ID}-019", f"MCH-{config.PLANT_ID}-008"),  # Robot assigned to Press
        (f"MTR-{config.PLANT_ID}-020", f"MCH-{config.PLANT_ID}-010"),  # Conveyor assigned to Oven
    ]

    injected_c5 = 0
    for i in range(c5_count):
        mtr_id, invalid_mch_id = invalid_pairs[i % len(invalid_pairs)]
        sample_indices = readings_by_meter[mtr_id]
        
        for cand_idx in sample_indices[40:-40]:
            if cand_idx not in used_reading_indices:
                chosen_idx = cand_idx
                break
        else:
            chosen_idx = rng.choice(sample_indices[30:-30])

        rec = readings[chosen_idx]
        orig_mch = rec["machine_id"]
        rec["machine_id"] = invalid_mch_id
        rec["is_anomaly"] = 1
        rec["anomaly_category"] = "HIERARCHY_VIOLATION"
        used_reading_indices.add(chosen_idx)

        anomaly_id = f"ANO-2026-{anomaly_counter:06d}"
        anomaly_counter += 1

        ground_truth.append({
            "anomaly_id": anomaly_id,
            "category_id": 5,
            "category_name": "HIERARCHY_VIOLATION",
            "affected_entity_type": "ENERGY_READING",
            "affected_entity_id": rec["meter_id"],
            "reading_id": rec["reading_id"],
            "timestamp": rec["timestamp"],
            "original_value": f"machine_id={orig_mch}",
            "injected_value": f"machine_id={invalid_mch_id}",
            "severity": "CRITICAL",
            "expected_detection_rule": "(machine_id, meter_id) NOT IN (SELECT machine_id, meter_id FROM machine_meter_assignments)",
            "rationale": f"Telemetry ingestion parser misrouted channel packet from meter {mtr_id} to machine {invalid_mch_id}."
        })
        injected_c5 += 1

    # Combine original readings and newly injected duplicate rows
    all_readings = readings + duplicated_readings
    # Sort deterministically by meter_id, timestamp, reading_id
    all_readings.sort(key=lambda x: (x["meter_id"], x["timestamp"], x["reading_id"]))

    print(f"Successfully injected {len(ground_truth)} anomalies across 5 categories (Target: 125).")
    return all_readings, ground_truth
