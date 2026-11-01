"""
Transaction Generator for YottaFlex Energy Analytics Platform
=============================================================
Generates 2,000 Production Batches, Maintenance Events, Machine Idle Periods,
and 172,800 Baseline 15-Minute Telemetry Energy Readings.
Enforces realistic physics and causal correlation between production and energy.
"""

from datetime import datetime, timedelta
import random
import math
from typing import List, Dict, Any, Tuple, Optional
import config
from src.business_logic.calculations import (
    get_effective_tariff,
    calculate_interval_energy,
    calculate_energy_cost,
    calculate_reactive_energy,
)

def generate_transactions(
    plants: List[Dict[str, Any]],
    meters: List[Dict[str, Any]],
    machines: List[Dict[str, Any]],
    shifts: List[Dict[str, Any]],
    weather_obs: List[Dict[str, Any]],
    seed: int = config.RANDOM_SEED
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Returns:
    - production_batches (2,000 rows)
    - maintenance_events (~80 rows)
    - machine_idle_periods (~450 rows)
    - energy_readings (172,800 baseline rows: 20 meters * 90 days * 96 intervals)
    """
    rng = random.Random(seed)
    
    start_dt = datetime.strptime(config.START_DATE_STR, "%Y-%m-%d %H:%M:%S")
    end_dt = datetime.strptime(config.END_DATE_STR, "%Y-%m-%d %H:%M:%S")
    total_intervals_per_meter = config.DAYS_OF_HISTORY * 24 * 4  # 8,640
    
    # Pre-index weather by timestamp (hour-aligned)
    weather_by_hour = {}
    for w in weather_obs:
        # Key by "YYYY-MM-DD HH"
        dt_key = w["observation_timestamp"][:13]
        weather_by_hour[dt_key] = w["dry_bulb_temperature_c"]

    # Map machines by machine_id
    machine_dict = {m["machine_id"]: m for m in machines}
    # Map meters by meter_id
    meter_dict = {m["meter_id"]: m for m in meters}
    # Find machine to meter mapping
    # MTR-005 -> MCH-001, etc.
    machine_to_meter = {}
    meter_to_machine = {}
    for i in range(1, 17):
        mch_id = f"MCH-{config.PLANT_ID}-{i:03d}"
        mtr_id = f"MTR-{config.PLANT_ID}-{i+4:03d}"
        machine_to_meter[mch_id] = mtr_id
        meter_to_machine[mtr_id] = mch_id

    feeder_children = {
        f"MTR-{config.PLANT_ID}-002": [f"MTR-{config.PLANT_ID}-{i:03d}" for i in [5, 6, 7, 8, 19]],
        f"MTR-{config.PLANT_ID}-003": [f"MTR-{config.PLANT_ID}-{i:03d}" for i in [9, 10, 11, 12, 20]],
        f"MTR-{config.PLANT_ID}-004": [f"MTR-{config.PLANT_ID}-{i:03d}" for i in [13, 14, 15, 16, 17, 18]],
    }

    # 1. Generate 2,000 Production Batches
    print("Generating 2,000 production batches...")
    batches = []
    product_skus = [
        "SKU-AERO-TURBINE-BLADE-01", "SKU-AUTO-TRANSMISSION-HOUSING-04",
        "SKU-ROBOTIC-ACTUATOR-ARM-09", "SKU-PRECISION-GEAR-BOX-12",
        "SKU-TITANIUM-IMPLANT-BRACKET-03", "SKU-DRONE-CHASSIS-CARBON-07",
        "SKU-EV-BATTERY-ENCLOSURE-22", "SKU-HYDRAULIC-VALVE-MANIFOLD-15"
    ]
    
    # We distribute 2,000 batches across the 90 days and across the primary manufacturing machines
    primary_machines = [f"MCH-{config.PLANT_ID}-{i:03d}" for i in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 16]]
    
    for b_idx in range(1, config.NUM_BATCHES + 1):
        batch_id = f"BATCH-2026-{b_idx:06d}"
        mch_id = rng.choice(primary_machines)
        
        # Pick random day and hour within the 90 days
        day_offset = rng.randint(0, config.DAYS_OF_HISTORY - 1)
        hour_start = rng.choice([6, 8, 10, 14, 16, 18, 22])
        b_start = start_dt + timedelta(days=day_offset, hours=hour_start, minutes=rng.choice([0, 15, 30, 45]))
        duration_hours = rng.uniform(2.5, 7.5)
        b_end = b_start + timedelta(hours=duration_hours)
        if b_end > end_dt:
            b_end = end_dt

        # Shift mapping
        start_hour = b_start.hour
        if 6 <= start_hour < 14:
            shift_id = "SHF-001"
        elif 14 <= start_hour < 22:
            shift_id = "SHF-002"
        else:
            shift_id = "SHF-003"

        planned = rng.randint(150, 1200)
        yield_rate = rng.uniform(0.92, 0.99)
        good = int(planned * yield_rate)
        scrap = planned - good

        batches.append({
            "batch_id": batch_id,
            "plant_id": config.PLANT_ID,
            "machine_id": mch_id,
            "shift_id": shift_id,
            "product_sku": rng.choice(product_skus),
            "planned_units": planned,
            "actual_good_units": good,
            "actual_scrap_units": scrap,
            "start_timestamp": b_start.strftime("%Y-%m-%d %H:%M:%S"),
            "end_timestamp": b_end.strftime("%Y-%m-%d %H:%M:%S"),
            "status": "COMPLETED",
        })

    # Sort batches deterministically
    batches.sort(key=lambda x: x["start_timestamp"])

    # 2. Generate Maintenance Events (~80 events across 90 days)
    print("Generating maintenance events...")
    maintenance_events = []
    maint_types = ["PREVENTIVE", "EMERGENCY_CORRECTIVE", "FILTER_CHANGEOVER", "LUBRICATION_OVERHAUL"]
    severities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

    for m_idx in range(1, 85):
        event_id = f"MNT-2026-{m_idx:04d}"
        mch_id = f"MCH-{config.PLANT_ID}-{rng.randint(1, 16):03d}"
        mtr_id = machine_to_meter[mch_id]
        
        day_offset = rng.randint(0, config.DAYS_OF_HISTORY - 1)
        m_start = start_dt + timedelta(days=day_offset, hours=rng.randint(0, 23))
        downtime = rng.uniform(45.0, 360.0)  # 45 mins to 6 hours
        m_end = m_start + timedelta(minutes=downtime)
        if m_end > end_dt:
            m_end = end_dt
            downtime = (m_end - m_start).total_seconds() / 60.0

        ev_type = rng.choice(maint_types)
        severity = "HIGH" if ev_type == "EMERGENCY_CORRECTIVE" else rng.choice(["LOW", "MEDIUM"])
        cost = round(downtime * rng.uniform(4.0, 12.0) + rng.uniform(100, 800), 2)

        maintenance_events.append({
            "event_id": event_id,
            "machine_id": mch_id,
            "meter_id": mtr_id,
            "event_type": ev_type,
            "severity": severity,
            "start_timestamp": m_start.strftime("%Y-%m-%d %H:%M:%S"),
            "end_timestamp": m_end.strftime("%Y-%m-%d %H:%M:%S"),
            "downtime_minutes": round(downtime, 2),
            "technician_notes": f"Standard {ev_type.lower().replace('_', ' ')} executed according to plant standard operating procedure.",
            "cost_usd": cost,
        })
    maintenance_events.sort(key=lambda x: x["start_timestamp"])

    # 3. Generate Machine Idle Periods (~450 events)
    print("Generating machine idle periods...")
    machine_idle_periods = []
    idle_reasons = ["OPERATOR_BREAK", "STARVED_MATERIAL", "BLOCKED_DOWNSTREAM", "UNPLANNED_CHANGEOVER", "OFF_SHIFT_STANDBY"]
    
    for i_idx in range(1, 480):
        idle_id = f"IDL-2026-{i_idx:05d}"
        mch_id = f"MCH-{config.PLANT_ID}-{rng.randint(1, 16):03d}"
        mtr_id = machine_to_meter[mch_id]
        mch = machine_dict[mch_id]

        day_offset = rng.randint(0, config.DAYS_OF_HISTORY - 1)
        i_start = start_dt + timedelta(days=day_offset, hours=rng.randint(0, 23), minutes=rng.choice([0, 15, 30, 45]))
        duration_min = rng.choice([15.0, 30.0, 45.0, 60.0, 90.0, 120.0])
        i_end = i_start + timedelta(minutes=duration_min)
        if i_end > end_dt:
            i_end = end_dt
            duration_min = max(15.0, (i_end - i_start).total_seconds() / 60.0)

        reason = rng.choice(idle_reasons)
        standby_kw = mch["standby_power_kw"]
        wasted_kwh = round(standby_kw * (duration_min / 60.0), 4)
        
        # Rate at that time
        ambient_temp = weather_by_hour.get(i_start.strftime("%Y-%m-%d %H"), 25.0)
        _, rate = get_effective_tariff(i_start, ambient_temp)
        wasted_cost = round(wasted_kwh * rate, 4)

        machine_idle_periods.append({
            "idle_id": idle_id,
            "machine_id": mch_id,
            "meter_id": mtr_id,
            "idle_reason": reason,
            "start_timestamp": i_start.strftime("%Y-%m-%d %H:%M:%S"),
            "end_timestamp": i_end.strftime("%Y-%m-%d %H:%M:%S"),
            "duration_minutes": duration_min,
            "energy_wasted_kwh": wasted_kwh,
            "cost_wasted_usd": wasted_cost,
        })
    machine_idle_periods.sort(key=lambda x: x["start_timestamp"])

    # Build fast interval schedule bitmasks/arrays for causal realism
    # 8,640 intervals per machine
    mch_has_batch = {m["machine_id"]: [False] * total_intervals_per_meter for m in machines}
    mch_is_idle = {m["machine_id"]: [False] * total_intervals_per_meter for m in machines}
    mch_in_maint = {m["machine_id"]: [False] * total_intervals_per_meter for m in machines}

    for b in batches:
        b_s = datetime.strptime(b["start_timestamp"], "%Y-%m-%d %H:%M:%S")
        b_e = datetime.strptime(b["end_timestamp"], "%Y-%m-%d %H:%M:%S")
        s_idx = max(0, min(total_intervals_per_meter - 1, int((b_s - start_dt).total_seconds() / 900)))
        e_idx = max(0, min(total_intervals_per_meter - 1, int((b_e - start_dt).total_seconds() / 900)))
        for i in range(s_idx, e_idx + 1):
            mch_has_batch[b["machine_id"]][i] = True

    for ev in maintenance_events:
        m_s = datetime.strptime(ev["start_timestamp"], "%Y-%m-%d %H:%M:%S")
        m_e = datetime.strptime(ev["end_timestamp"], "%Y-%m-%d %H:%M:%S")
        s_idx = max(0, min(total_intervals_per_meter - 1, int((m_s - start_dt).total_seconds() / 900)))
        e_idx = max(0, min(total_intervals_per_meter - 1, int((m_e - start_dt).total_seconds() / 900)))
        for i in range(s_idx, e_idx + 1):
            mch_in_maint[ev["machine_id"]][i] = True

    for idl in machine_idle_periods:
        i_s = datetime.strptime(idl["start_timestamp"], "%Y-%m-%d %H:%M:%S")
        i_e = datetime.strptime(idl["end_timestamp"], "%Y-%m-%d %H:%M:%S")
        s_idx = max(0, min(total_intervals_per_meter - 1, int((i_s - start_dt).total_seconds() / 900)))
        e_idx = max(0, min(total_intervals_per_meter - 1, int((i_e - start_dt).total_seconds() / 900)))
        for i in range(s_idx, e_idx + 1):
            mch_is_idle[idl["machine_id"]][i] = True

    # 4. Generate 172,800 Baseline Energy Readings
    # 20 meters * 8,640 intervals = 172,800 records
    print("Generating 172,800 baseline energy readings (20 meters * 8,640 intervals)...")
    energy_readings = []

    for interval_idx in range(total_intervals_per_meter):
        cur_time = start_dt + timedelta(minutes=interval_idx * config.INTERVAL_MINUTES)
        ts_str = cur_time.strftime("%Y-%m-%d %H:%M:%S")
        ts_iso = cur_time.strftime("%Y%m%dT%H%M%S")
        hour_key = cur_time.strftime("%Y-%m-%d %H")
        ambient_temp = weather_by_hour.get(hour_key, 25.0)
        tariff_id, rate_per_kwh = get_effective_tariff(cur_time, ambient_temp)
        
        # Weekday/weekend & diurnal operational factor
        is_weekend = cur_time.weekday() >= 5
        hour = cur_time.hour
        
        # Sub-meter readings for the 16 machines (meters 005 to 020)
        submeter_kw = {}

        for m_num in range(5, 21):
            mtr_id = f"MTR-{config.PLANT_ID}-{m_num:03d}"
            mch_id = meter_to_machine[mtr_id]
            mch = machine_dict[mch_id]

            # Determine operating mode
            # Chillers (MCH-013, MCH-014) are weather-dependent continuous systems
            if mch["category"] == "CHILLER_PLANT":
                cdd = max(0.0, (ambient_temp - 18.33) / 10.0)
                base_load = mch["standby_power_kw"] + 35.0
                dynamic_load = cdd * 32.0 + rng.uniform(-3.0, 3.0)
                kw = round(min(mch["rated_power_kw"], max(mch["standby_power_kw"], base_load + dynamic_load)), 3)
            elif mch["category"] == "ROTARY_SCREW_COMPRESSOR":
                # Air compressors run continuous modulated trim + baseload
                load_factor = 0.55 if is_weekend else (0.85 if 6 <= hour <= 22 else 0.65)
                kw = round(mch["standby_power_kw"] + (mch["operating_power_kw"] - mch["standby_power_kw"]) * load_factor + rng.uniform(-2.5, 2.5), 3)
            elif mch["category"] == "INDUSTRIAL_OVEN":
                # Thermal ovens maintain heat
                load_factor = 0.40 if is_weekend else (0.90 if 6 <= hour <= 22 else 0.60)
                kw = round(mch["standby_power_kw"] + (mch["operating_power_kw"] - mch["standby_power_kw"]) * load_factor + rng.uniform(-3.0, 3.0), 3)
            else:
                # Production machining & assembly cells: strictly causal
                in_maint = mch_in_maint[mch_id][interval_idx]
                is_idle = mch_is_idle[mch_id][interval_idx]
                has_batch = mch_has_batch[mch_id][interval_idx]

                if in_maint:
                    # Equipment de-energized during maintenance; auxiliary control circuits only
                    kw = round(rng.uniform(0.15, 0.45), 3)
                elif is_idle:
                    # Confirmed idle/standby power
                    kw = round(mch["standby_power_kw"] * rng.uniform(0.96, 1.04), 3)
                elif has_batch:
                    # Active production: nominal operating power + physical cutting resistance variation
                    kw = round(mch["operating_power_kw"] * rng.uniform(0.92, 1.04), 3)
                else:
                    # Off-shift or inter-batch standby
                    kw = round(mch["standby_power_kw"] * rng.uniform(0.94, 1.06), 3)

            submeter_kw[mtr_id] = kw

            # Derived energy and cost calculations
            kwh = calculate_interval_energy(kw, 15)
            cost = calculate_energy_cost(kwh, rate_per_kwh)
            kvarh = calculate_reactive_energy(kwh, 0.95)

            reading_id = f"ENG-{mtr_id}-{ts_iso}"
            energy_readings.append({
                "reading_id": reading_id,
                "meter_id": mtr_id,
                "machine_id": mch_id,
                "timestamp": ts_str,
                "interval_minutes": 15,
                "power_demand_kw": kw,
                "energy_consumed_kwh": kwh,
                "reactive_energy_kvarh": kvarh,
                "power_factor": 0.95,
                "tariff_id": tariff_id,
                "cost_usd": cost,
                "is_anomaly": 0,
                "anomaly_category": None,
            })

        # Calculate Feeder Readings (MTR-002, 003, 004)
        # Sum of respective child sub-meters + 2.5% distribution busbar loss
        feeder_kw = {}
        for fdr_id, child_ids in feeder_children.items():
            child_sum_kw = sum(submeter_kw[cid] for cid in child_ids)
            f_kw = round(child_sum_kw * 1.025, 3)
            feeder_kw[fdr_id] = f_kw

            f_kwh = calculate_interval_energy(f_kw, 15)
            f_cost = calculate_energy_cost(f_kwh, rate_per_kwh)
            f_kvarh = calculate_reactive_energy(f_kwh, 0.94)

            reading_id = f"ENG-{fdr_id}-{ts_iso}"
            energy_readings.append({
                "reading_id": reading_id,
                "meter_id": fdr_id,
                "machine_id": None,
                "timestamp": ts_str,
                "interval_minutes": 15,
                "power_demand_kw": f_kw,
                "energy_consumed_kwh": f_kwh,
                "reactive_energy_kvarh": f_kvarh,
                "power_factor": 0.94,
                "tariff_id": tariff_id,
                "cost_usd": f_cost,
                "is_anomaly": 0,
                "anomaly_category": None,
            })

        # Calculate Main Incomer Reading (MTR-001)
        # Sum of 3 feeders + facility baseload (lighting, IT, office HVAC ~55 kW)
        facility_base_load = 55.0 + rng.uniform(-2.0, 2.0)
        main_kw = round(sum(feeder_kw.values()) + facility_base_load, 3)
        main_kwh = calculate_interval_energy(main_kw, 15)
        main_cost = calculate_energy_cost(main_kwh, rate_per_kwh)
        main_kvarh = calculate_reactive_energy(main_kwh, 0.93)

        reading_id = f"ENG-MTR-{config.PLANT_ID}-001-{ts_iso}"
        energy_readings.append({
            "reading_id": reading_id,
            "meter_id": f"MTR-{config.PLANT_ID}-001",
            "machine_id": None,
            "timestamp": ts_str,
            "interval_minutes": 15,
            "power_demand_kw": main_kw,
            "energy_consumed_kwh": main_kwh,
            "reactive_energy_kvarh": main_kvarh,
            "power_factor": 0.93,
            "tariff_id": tariff_id,
            "cost_usd": main_cost,
            "is_anomaly": 0,
            "anomaly_category": None,
        })

    print(f"Generated {len(energy_readings)} clean baseline energy readings.")
    return batches, maintenance_events, machine_idle_periods, energy_readings
