"""
Business Logic & Calculations Engine for YottaFlex Energy Platform
==================================================================
Implements actual industrial physics, electrical engineering formulas,
and financial calculations. Derived values are strictly computed from source data.
"""

from datetime import datetime
import math
from typing import Dict, Any, List, Optional, Tuple

def get_effective_tariff(
    dt: datetime,
    ambient_temp_c: float = 25.0,
    tariffs_by_id: Optional[Dict[str, Dict[str, Any]]] = None
) -> Tuple[str, float]:
    """
    Resolves the effective tariff ID and rate ($/kWh) for a given local datetime and weather condition.
    Tariff rules:
    - Weekend: TAR-2026-001 (OFF_PEAK, $0.0650)
    - Critical Peak Event: Summer weekday between 14:00 and 18:00 when ambient_temp_c >= 38.0°C (TAR-2026-004, $0.4500)
    - Weekday 13:00 to 19:00: TAR-2026-003 (ON_PEAK, $0.2250)
    - Weekday 07:00 to 13:00, 19:00 to 22:00: TAR-2026-002 (SHOULDER, $0.1280)
    - Weekday 22:00 to 07:00: TAR-2026-001 (OFF_PEAK, $0.0650)
    """
    is_weekend = dt.weekday() >= 5
    hour = dt.hour

    if is_weekend:
        return "TAR-2026-001", 0.0650

    # Critical Peak Event in hot summer months
    if 6 <= dt.month <= 9 and 14 <= hour < 18 and ambient_temp_c >= 38.0:
        return "TAR-2026-004", 0.4500

    # On Peak
    if 13 <= hour < 19:
        return "TAR-2026-003", 0.2250

    # Shoulder
    if (7 <= hour < 13) or (19 <= hour < 22):
        return "TAR-2026-002", 0.1280

    # Off Peak
    return "TAR-2026-001", 0.0650

def calculate_interval_energy(power_kw: float, interval_minutes: int = 15) -> float:
    """
    Computes energy in kWh from active power (kW) and interval duration (minutes).
    E (kWh) = P (kW) * (minutes / 60)
    """
    return round(power_kw * (interval_minutes / 60.0), 4)

def calculate_energy_cost(energy_kwh: float, rate_per_kwh_usd: float) -> float:
    """Computes monetary energy cost in USD."""
    return round(energy_kwh * rate_per_kwh_usd, 4)

def calculate_reactive_energy(energy_kwh: float, power_factor: float = 0.95) -> float:
    """
    Computes reactive energy in kVARh from active energy and power factor.
    Q = P * tan(acos(PF))
    """
    pf_clamped = max(0.1, min(0.999, power_factor))
    tan_phi = math.tan(math.acos(pf_clamped))
    return round(energy_kwh * tan_phi, 4)

def calculate_energy_intensity(total_kwh: float, good_units: int) -> float:
    """Computes Specific Energy Consumption (SEC): kWh consumed per good unit produced."""
    if good_units <= 0:
        return 0.0
    return round(total_kwh / float(good_units), 4)

def calculate_idle_waste(standby_power_kw: float, duration_minutes: float, rate_per_kwh_usd: float) -> Tuple[float, float]:
    """Computes kWh wasted during machine idle periods and monetary loss in USD."""
    hours = duration_minutes / 60.0
    wasted_kwh = round(standby_power_kw * hours, 4)
    wasted_usd = round(wasted_kwh * rate_per_kwh_usd, 4)
    return wasted_kwh, wasted_usd
