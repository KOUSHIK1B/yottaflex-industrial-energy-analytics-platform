"""
Reference Data Generator for YottaFlex Energy Analytics Platform
================================================================
Generates Shifts, Tariffs (with deterministic IDs), and Weather Observations
for the 90-day simulation window using fixed random seed.
"""

from datetime import datetime, timedelta
import math
import random
from typing import List, Dict, Any, Tuple
import config

def generate_reference_data(seed: int = config.RANDOM_SEED) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Generates:
    - 3 Operating Shifts (Morning, Afternoon, Night)
    - 4 Time-of-Use Tariffs with deterministic IDs TAR-2026-001 to TAR-2026-004
    - 2,160 Hourly Weather Observations (90 days * 24 hours)
    """
    rng = random.Random(seed + 100)

    # 1. Shifts
    shifts = [
        {
            "shift_id": "SHF-001",
            "plant_id": config.PLANT_ID,
            "name": "Morning Production Shift",
            "start_time_local": "06:00:00",
            "end_time_local": "14:00:00",
            "duration_hours": 8.0,
            "standard_manning_level": 42,
            "shift_multiplier": 1.05,
        },
        {
            "shift_id": "SHF-002",
            "plant_id": config.PLANT_ID,
            "name": "Afternoon Peak Shift",
            "start_time_local": "14:00:00",
            "end_time_local": "22:00:00",
            "duration_hours": 8.0,
            "standard_manning_level": 38,
            "shift_multiplier": 1.00,
        },
        {
            "shift_id": "SHF-003",
            "plant_id": config.PLANT_ID,
            "name": "Night Low-Energy Shift",
            "start_time_local": "22:00:00",
            "end_time_local": "06:00:00",
            "duration_hours": 8.0,
            "standard_manning_level": 18,
            "shift_multiplier": 0.85,
        },
    ]

    # 2. Tariffs (Deterministic IDs: TAR-2026-001..004)
    tariffs = [
        {
            "tariff_id": "TAR-2026-001",
            "plant_id": config.PLANT_ID,
            "tariff_code": "TOU-OFFPEAK-LV",
            "name": "Off-Peak Base Power Tariff",
            "period_type": "OFF_PEAK",
            "rate_per_kwh_usd": 0.0650,
            "demand_charge_per_kw_usd": 5.0000,
            "start_hour": 22,
            "end_hour": 7,
            "is_weekend_applicable": 1,
            "effective_from": "2026-01-01",
            "effective_to": "2026-12-31",
        },
        {
            "tariff_id": "TAR-2026-002",
            "plant_id": config.PLANT_ID,
            "tariff_code": "TOU-SHOULDER-LV",
            "name": "Shoulder Commercial Tariff",
            "period_type": "SHOULDER",
            "rate_per_kwh_usd": 0.1280,
            "demand_charge_per_kw_usd": 10.0000,
            "start_hour": 7,
            "end_hour": 13,
            "is_weekend_applicable": 0,
            "effective_from": "2026-01-01",
            "effective_to": "2026-12-31",
        },
        {
            "tariff_id": "TAR-2026-003",
            "plant_id": config.PLANT_ID,
            "tariff_code": "TOU-ONPEAK-LV",
            "name": "On-Peak High Demand Tariff",
            "period_type": "ON_PEAK",
            "rate_per_kwh_usd": 0.2250,
            "demand_charge_per_kw_usd": 18.5000,
            "start_hour": 13,
            "end_hour": 19,
            "is_weekend_applicable": 0,
            "effective_from": "2026-01-01",
            "effective_to": "2026-12-31",
        },
        {
            "tariff_id": "TAR-2026-004",
            "plant_id": config.PLANT_ID,
            "tariff_code": "TOU-CRITPEAK-LV",
            "name": "Critical Peak Summer Event Tariff",
            "period_type": "CRITICAL_PEAK",
            "rate_per_kwh_usd": 0.4500,
            "demand_charge_per_kw_usd": 25.0000,
            "start_hour": 14,
            "end_hour": 18,
            "is_weekend_applicable": 0,
            "effective_from": "2026-06-01",
            "effective_to": "2026-09-30",
        },
    ]

    # 3. Weather Observations (Hourly over 90 days = 2160 readings)
    start_dt = datetime.strptime(config.START_DATE_STR, "%Y-%m-%d %H:%M:%S")
    weather_observations = []
    
    total_hours = config.DAYS_OF_HISTORY * 24
    for h in range(total_hours):
        obs_time = start_dt + timedelta(hours=h)
        hour_of_day = obs_time.hour
        day_of_year = obs_time.timetuple().tm_yday
        
        # Diurnal temperature cycle: peak around 15:00, trough around 05:00
        diurnal_rad = 2 * math.pi * (hour_of_day - 5) / 24.0
        # Seasonal trend: July/August hotter (~34°C avg), October cooler (~24°C avg)
        seasonal_base = 34.0 - (10.0 * (h / total_hours))
        
        # Add random weather fluctuation
        noise = rng.uniform(-2.5, 2.5)
        temp_c = seasonal_base + (6.0 * math.sin(diurnal_rad)) + noise
        temp_c = round(max(14.0, min(42.0, temp_c)), 2)

        # Humidity inverse to temperature
        humidity = round(max(25.0, min(95.0, 75.0 - (temp_c * 0.8) + rng.uniform(-5, 5))), 2)

        # Solar GHI: 0 at night, peak ~900 W/m2 at solar noon
        if 6 <= hour_of_day <= 19:
            solar_sin = math.sin(math.pi * (hour_of_day - 6) / 13.0)
            solar_ghi = round(max(0.0, 850.0 * solar_sin + rng.uniform(-30, 30)), 2)
        else:
            solar_ghi = 0.0

        # Cooling degree factor = max(0, temp_c - 18.33) / 10.0
        cdd = round(max(0.0, (temp_c - 18.33) / 10.0), 3)

        weather_id = f"WTH-{config.PLANT_ID}-{obs_time.strftime('%Y%m%d%H%M')}"
        weather_observations.append({
            "weather_id": weather_id,
            "plant_id": config.PLANT_ID,
            "observation_timestamp": obs_time.strftime("%Y-%m-%d %H:%M:%S"),
            "dry_bulb_temperature_c": temp_c,
            "relative_humidity_pct": humidity,
            "solar_ghi_w_per_m2": solar_ghi,
            "cooling_degree_load_factor": cdd,
        })

    return shifts, tariffs, weather_observations
