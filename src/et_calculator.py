"""
et_calculator.py
Evapotranspiration estimation using the FAO Penman-Monteith method.
Reference: FAO Irrigation and Drainage Paper No. 56
"""

import math
from dataclasses import dataclass
from typing import Optional


@dataclass
class SensorData:
    temperature_c: float        # Mean daily temperature (°C)
    humidity_pct: float         # Relative humidity (%)
    wind_speed_ms: float        # Wind speed at 2m height (m/s)
    solar_radiation: float      # Solar radiation (MJ/m²/day)
    elevation_m: float = 350.0  # Site elevation above sea level (m)
    latitude_deg: float = 18.0  # Latitude in degrees


def compute_et0(data: SensorData, day_of_year: int = 180) -> float:
    """
    Compute reference evapotranspiration ET₀ (mm/day)
    using the Penman-Monteith equation.

    Args:
        data: SensorData object with environmental measurements
        day_of_year: Julian day (1-365)

    Returns:
        ET₀ in mm/day
    """
    T = data.temperature_c
    RH = data.humidity_pct
    u2 = data.wind_speed_ms
    Rs = data.solar_radiation
    z = data.elevation_m
    phi = math.radians(data.latitude_deg)

    # ── Atmospheric pressure (kPa) ─────────────────────────────
    P = 101.3 * ((293 - 0.0065 * z) / 293) ** 5.26

    # ── Psychrometric constant γ (kPa/°C) ─────────────────────
    gamma = 0.000665 * P

    # ── Saturation vapor pressure es (kPa) ────────────────────
    es = 0.6108 * math.exp((17.27 * T) / (T + 237.3))

    # ── Actual vapor pressure ea (kPa) ────────────────────────
    ea = es * (RH / 100.0)

    # ── Slope of vapor pressure curve Δ (kPa/°C) ─────────────
    delta = (4098 * es) / ((T + 237.3) ** 2)

    # ── Extra-terrestrial radiation Ra (MJ/m²/day) ────────────
    dr = 1 + 0.033 * math.cos(2 * math.pi * day_of_year / 365)
    solar_dec = 0.409 * math.sin(2 * math.pi * day_of_year / 365 - 1.39)
    omega_s = math.acos(-math.tan(phi) * math.tan(solar_dec))
    Ra = (24 * 60 / math.pi) * 0.0820 * dr * (
        omega_s * math.sin(phi) * math.sin(solar_dec)
        + math.cos(phi) * math.cos(solar_dec) * math.sin(omega_s)
    )

    # ── Clear-sky solar radiation Rso ─────────────────────────
    Rso = (0.75 + 2e-5 * z) * Ra

    # ── Net shortwave radiation Rns ───────────────────────────
    alpha = 0.23  # Albedo for reference grass crop
    Rns = (1 - alpha) * Rs

    # ── Net outgoing longwave radiation Rnl ───────────────────
    sigma = 4.903e-9  # Stefan-Boltzmann (MJ/m²/day)
    TK = T + 273.16
    Rnl = sigma * (TK ** 4) * (0.34 - 0.14 * math.sqrt(ea)) * (
        1.35 * (Rs / Rso) - 0.35
    )

    # ── Net radiation Rn ──────────────────────────────────────
    Rn = Rns - Rnl

    # ── Soil heat flux G (≈ 0 for daily) ─────────────────────
    G = 0.0

    # ── Penman-Monteith ET₀ ───────────────────────────────────
    numerator = (0.408 * delta * (Rn - G) +
                 gamma * (900 / (T + 273)) * u2 * (es - ea))
    denominator = delta + gamma * (1 + 0.34 * u2)

    et0 = numerator / denominator
    return max(et0, 0.0)


def compute_crop_et(et0: float, crop_type: str, growth_stage: str) -> float:
    """
    Compute actual crop evapotranspiration ETc = Kc × ET₀.

    Args:
        et0: Reference ET₀ (mm/day)
        crop_type: e.g., 'tomato', 'wheat', 'maize', 'rice'
        growth_stage: 'initial', 'vegetative', 'flowering', 'ripening'

    Returns:
        ETc in mm/day
    """
    # Crop coefficients Kc from FAO-56 Table 12
    kc_table = {
        "tomato":  {"initial": 0.40, "vegetative": 0.75, "flowering": 1.15, "ripening": 0.80},
        "wheat":   {"initial": 0.30, "vegetative": 0.70, "flowering": 1.15, "ripening": 0.25},
        "maize":   {"initial": 0.30, "vegetative": 0.70, "flowering": 1.20, "ripening": 0.35},
        "rice":    {"initial": 1.05, "vegetative": 1.05, "flowering": 1.20, "ripening": 0.75},
        "cotton":  {"initial": 0.35, "vegetative": 0.75, "flowering": 1.15, "ripening": 0.50},
        "soybean": {"initial": 0.40, "vegetative": 0.80, "flowering": 1.15, "ripening": 0.50},
        "default": {"initial": 0.35, "vegetative": 0.75, "flowering": 1.10, "ripening": 0.60},
    }

    crop_key = crop_type.lower() if crop_type.lower() in kc_table else "default"
    stage_key = growth_stage.lower() if growth_stage.lower() in kc_table[crop_key] else "vegetative"
    kc = kc_table[crop_key][stage_key]

    return et0 * kc


def irrigation_deficit(etc_mm: float, rainfall_mm: float, efficiency: float = 0.85) -> float:
    """
    Compute net irrigation requirement.

    Args:
        etc_mm: Crop ET demand (mm/day)
        rainfall_mm: Effective rainfall (mm/day)
        efficiency: Irrigation system efficiency (0-1)

    Returns:
        Net irrigation water required (mm/day), 0 if rainfall sufficient
    """
    deficit = etc_mm - rainfall_mm
    if deficit <= 0:
        return 0.0
    return deficit / efficiency


if __name__ == "__main__":
    sample = SensorData(
        temperature_c=28.5,
        humidity_pct=65.0,
        wind_speed_ms=2.1,
        solar_radiation=22.0,
        elevation_m=260.0,
        latitude_deg=17.98  # Warangal, India
    )

    et0 = compute_et0(sample, day_of_year=150)
    etc = compute_crop_et(et0, "tomato", "flowering")
    deficit = irrigation_deficit(etc, rainfall_mm=2.0)

    print(f"ET₀  : {et0:.2f} mm/day")
    print(f"ETc  : {etc:.2f} mm/day  (Tomato - Flowering stage)")
    print(f"Net Irrigation Requirement: {deficit:.2f} mm/day")
