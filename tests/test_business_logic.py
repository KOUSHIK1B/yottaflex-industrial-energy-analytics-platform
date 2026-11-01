"""
Business Logic & Calculations Tests
===================================
Tests energy interval physics (kW to kWh), TOU tariff assignments,
Specific Energy Consumption (SEC), and idle wastage math.
"""

from datetime import datetime
import pytest
from src.business_logic.calculations import (
    calculate_interval_energy,
    calculate_energy_cost,
    calculate_energy_intensity,
    calculate_idle_waste,
    get_effective_tariff,
)

def test_interval_energy_physics():
    # 100 kW load for 15 minutes = 25.0 kWh
    kwh = calculate_interval_energy(100.0, 15)
    assert kwh == 25.0

    # 48.0 kW load for 15 minutes = 12.0 kWh
    kwh_48 = calculate_interval_energy(48.0, 15)
    assert kwh_48 == 12.0

    # 0 kW load = 0 kWh
    assert calculate_interval_energy(0.0, 15) == 0.0

def test_energy_costing_math():
    # 25 kWh at On-Peak ($0.2250) = $5.625
    cost = calculate_energy_cost(25.0, 0.2250)
    assert cost == 5.625

    # 100 kWh at Off-Peak ($0.0650) = $6.50
    assert calculate_energy_cost(100.0, 0.0650) == 6.50

def test_tariff_time_of_use_resolution():
    # Weekday 14:00 (On-Peak)
    dt_weekday_peak = datetime(2026, 8, 12, 14, 30)
    t_id, rate = get_effective_tariff(dt_weekday_peak, ambient_temp_c=30.0)
    assert t_id == "TAR-2026-003"
    assert rate == 0.2250

    # Weekend 14:00 (Should be Off-Peak regardless of hour)
    dt_weekend = datetime(2026, 8, 15, 14, 30)  # Saturday
    t_id_wknd, rate_wknd = get_effective_tariff(dt_weekend, ambient_temp_c=32.0)
    assert t_id_wknd == "TAR-2026-001"
    assert rate_wknd == 0.0650

    # Critical Peak Event: Summer weekday afternoon with ambient temp >= 38.0°C
    dt_summer_hot = datetime(2026, 8, 12, 16, 0)
    t_id_crit, rate_crit = get_effective_tariff(dt_summer_hot, ambient_temp_c=39.5)
    assert t_id_crit == "TAR-2026-004"
    assert rate_crit == 0.4500

def test_energy_intensity_calculation():
    # 500 kWh for 250 units = 2.0 kWh/unit
    sec = calculate_energy_intensity(500.0, 250)
    assert sec == 2.0

    # Edge case: 0 units produced does not throw ZeroDivisionError
    assert calculate_energy_intensity(500.0, 0) == 0.0

def test_idle_waste_calculation():
    # 18.5 kW standby load for 60 minutes at $0.128/kWh
    wasted_kwh, wasted_usd = calculate_idle_waste(18.5, 60.0, 0.1280)
    assert wasted_kwh == 18.5
    assert wasted_usd == round(18.5 * 0.1280, 4)
