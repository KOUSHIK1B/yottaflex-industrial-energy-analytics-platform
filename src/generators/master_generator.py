"""
Master Data Generator for YottaFlex Energy Analytics Platform
============================================================
Generates Plants, Meters (with strict hierarchy), Machines,
and Machine-Meter Assignments (bridge table) with deterministic IDs.
"""

from typing import List, Dict, Any, Tuple
import config

def generate_master_data() -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Generates:
    - 1 Plant
    - 20 Meters (Main Incomer -> 3 Sub-Feeders -> 16 Sub-meters)
    - 16 Machines with realistic rated/standby/operating kW
    - 16 Machine-Meter Assignments (bridge table)
    """
    # 1. Plant
    plants = [{
        "plant_id": config.PLANT_ID,
        "name": config.PLANT_NAME,
        "industry_type": "Precision Metals & Robotics Manufacturing",
        "country": "USA",
        "state": "TX",
        "city": "Austin",
        "timezone": config.TIMEZONE,
        "grid_connection_voltage_kv": 13.80,
        "contracted_peak_capacity_kw": 2500.00,
        "created_at": "2026-01-01 00:00:00",
    }]

    # 2. Meters (20 meters total: 1 main incomer, 3 cell feeders, 16 sub-meters)
    # ID format: MTR-<plant-id>-001 to 020
    meter_specs = [
        # Main Incomer
        ("001", None, "Utility 13.8kV Main Incomer Meter", "MAIN_INCOMER", "kWh", 13800.0, 1500.0),
        # 3 Sub-Feeders
        ("002", "MTR-PLT-001-001", "Feeder A: CNC & Milling Center Substation", "SUB_FEEDER", "kWh", 480.0, 1200.0),
        ("003", "MTR-PLT-001-001", "Feeder B: Heavy Molding & Press Substation", "SUB_FEEDER", "kWh", 480.0, 1000.0),
        ("004", "MTR-PLT-001-001", "Feeder C: Thermal, Chiller & Utilities Busbar", "SUB_FEEDER", "kWh", 480.0, 1000.0),
        # 16 Machine Point Sub-Meters
        ("005", "MTR-PLT-001-002", "Meter - 5-Axis CNC Milling Center #1", "MACHINE_POINT", "kWh", 480.0, 150.0),
        ("006", "MTR-PLT-001-002", "Meter - 5-Axis CNC Milling Center #2", "MACHINE_POINT", "kWh", 480.0, 150.0),
        ("007", "MTR-PLT-001-002", "Meter - High-Speed CNC Lathe #1", "MACHINE_POINT", "kWh", 480.0, 100.0),
        ("008", "MTR-PLT-001-002", "Meter - High-Speed CNC Lathe #2", "MACHINE_POINT", "kWh", 480.0, 100.0),
        ("009", "MTR-PLT-001-003", "Meter - Hydraulic Injection Molder 350T", "MACHINE_POINT", "kWh", 480.0, 250.0),
        ("010", "MTR-PLT-001-003", "Meter - Electric Injection Molder 180T", "MACHINE_POINT", "kWh", 480.0, 180.0),
        ("011", "MTR-PLT-001-003", "Meter - Precision Injection Molder 120T", "MACHINE_POINT", "kWh", 480.0, 140.0),
        ("012", "MTR-PLT-001-003", "Meter - Heavy Stamping Press 500T", "MACHINE_POINT", "kWh", 480.0, 300.0),
        ("013", "MTR-PLT-001-004", "Meter - Continuous Thermal Curing Oven #1", "MACHINE_POINT", "kWh", 480.0, 350.0),
        ("014", "MTR-PLT-001-004", "Meter - Batch Heat Treatment Oven #2", "MACHINE_POINT", "kWh", 480.0, 250.0),
        ("015", "MTR-PLT-001-004", "Meter - Central Rotary Screw Compressor #1", "MACHINE_POINT", "kWh", 480.0, 200.0),
        ("016", "MTR-PLT-001-004", "Meter - Central Rotary Screw Compressor #2", "MACHINE_POINT", "kWh", 480.0, 200.0),
        ("017", "MTR-PLT-001-004", "Meter - Water-Cooled Central Chiller #1", "MACHINE_POINT", "kWh", 480.0, 300.0),
        ("018", "MTR-PLT-001-004", "Meter - Water-Cooled Central Chiller #2", "MACHINE_POINT", "kWh", 480.0, 300.0),
        ("019", "MTR-PLT-001-002", "Meter - Automated 6-Axis Assembly Cell", "MACHINE_POINT", "kWh", 480.0, 80.0),
        ("020", "MTR-PLT-001-003", "Meter - Main Facility Overhead Conveyor Loop", "MACHINE_POINT", "kWh", 480.0, 80.0),
    ]

    meters = []
    for num, parent_id, name, m_type, unit, volt, curr in meter_specs:
        meter_id = f"MTR-{config.PLANT_ID}-{num}"
        meters.append({
            "meter_id": meter_id,
            "plant_id": config.PLANT_ID,
            "parent_meter_id": parent_id,
            "name": name,
            "meter_type": m_type,
            "measurement_unit": unit,
            "voltage_rating_v": volt,
            "current_rating_a": curr,
            "installation_date": "2025-06-01",
            "status": "ACTIVE",
        })

    # 3. Machines (16 machines mapped to meters 005 through 020)
    # ID format: MCH-<plant-id>-001 to 016
    machine_specs = [
        ("001", "5-Axis CNC Milling Center Alpha", "CNC_MILLING", 75.0, 4.5, 48.0, "2025-06-10", "MTR-PLT-001-005"),
        ("002", "5-Axis CNC Milling Center Beta", "CNC_MILLING", 75.0, 4.5, 46.5, "2025-06-10", "MTR-PLT-001-006"),
        ("003", "High-Speed CNC Lathe Gamma", "CNC_MILLING", 45.0, 3.2, 32.0, "2025-06-15", "MTR-PLT-001-007"),
        ("004", "High-Speed CNC Lathe Delta", "CNC_MILLING", 45.0, 3.2, 31.5, "2025-06-15", "MTR-PLT-001-008"),
        ("005", "Hydraulic Injection Molder 350T", "INJECTION_MOLDING", 120.0, 8.5, 88.0, "2025-07-01", "MTR-PLT-001-009"),
        ("006", "Electric Injection Molder 180T", "INJECTION_MOLDING", 85.0, 4.0, 58.0, "2025-07-01", "MTR-PLT-001-010"),
        ("007", "Precision Injection Molder 120T", "INJECTION_MOLDING", 65.0, 3.5, 42.0, "2025-07-05", "MTR-PLT-001-011"),
        ("008", "Heavy Stamping Press 500T", "STAMPING_PRESS", 150.0, 7.0, 95.0, "2025-07-10", "MTR-PLT-001-012"),
        ("009", "Continuous Thermal Curing Oven", "INDUSTRIAL_OVEN", 160.0, 18.0, 125.0, "2025-07-15", "MTR-PLT-001-013"),
        ("010", "Batch Heat Treatment Oven", "INDUSTRIAL_OVEN", 110.0, 12.0, 78.0, "2025-07-15", "MTR-PLT-001-014"),
        ("011", "Central Rotary Screw Compressor #1", "ROTARY_SCREW_COMPRESSOR", 90.0, 18.5, 72.0, "2025-06-20", "MTR-PLT-001-015"),
        ("012", "Central Rotary Screw Compressor #2", "ROTARY_SCREW_COMPRESSOR", 90.0, 18.5, 70.0, "2025-06-20", "MTR-PLT-001-016"),
        ("013", "Water-Cooled Central Chiller #1", "CHILLER_PLANT", 140.0, 22.0, 98.0, "2025-06-25", "MTR-PLT-001-017"),
        ("014", "Water-Cooled Central Chiller #2", "CHILLER_PLANT", 140.0, 22.0, 94.0, "2025-06-25", "MTR-PLT-001-018"),
        ("015", "Automated 6-Axis Assembly Cell", "AUTOMATED_ASSEMBLY_ROBOT", 35.0, 2.5, 21.0, "2025-08-01", "MTR-PLT-001-019"),
        ("016", "Main Overhead Conveyor Loop", "CONVEYOR_SYSTEM", 30.0, 2.0, 18.0, "2025-08-01", "MTR-PLT-001-020"),
    ]

    machines = []
    assignments = []
    for num, name, cat, rated, standby, oper, comm_date, meter_id in machine_specs:
        machine_id = f"MCH-{config.PLANT_ID}-{num}"
        machines.append({
            "machine_id": machine_id,
            "plant_id": config.PLANT_ID,
            "name": name,
            "category": cat,
            "rated_power_kw": rated,
            "standby_power_kw": standby,
            "operating_power_kw": oper,
            "commissioning_date": comm_date,
            "lifecycle_state": "OPERATIONAL",
        })
        assignments.append({
            "assignment_id": f"ASN-{machine_id}-{meter_id}",
            "machine_id": machine_id,
            "meter_id": meter_id,
            "effective_from": "2026-01-01 00:00:00",
            "effective_to": None,
            "allocation_percentage": 100.0,
            "is_primary_meter": 1,
        })

    return plants, meters, machines, assignments
