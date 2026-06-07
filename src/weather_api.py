"""
weather_api.py
Fetch current weather and forecast from OpenWeatherMap API.
"""

import os
import requests
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

OWM_BASE = "https://api.openweathermap.org/data/2.5"


def get_current_weather(location: str, api_key: str) -> dict:
    """
    Fetch current weather for a location.

    Args:
        location: City name, e.g., "Warangal,IN"
        api_key: OpenWeatherMap API key

    Returns:
        dict with temperature, humidity, wind_speed, description
    """
    url = f"{OWM_BASE}/weather"
    params = {"q": location, "appid": api_key, "units": "metric"}

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        logger.error(f"Weather API error: {e}")
        return {}

    return {
        "temperature_c": data["main"]["temp"],
        "humidity_pct": data["main"]["humidity"],
        "wind_speed_ms": data["wind"]["speed"],
        "description": data["weather"][0]["description"],
        "cloud_cover_pct": data.get("clouds", {}).get("all", 0),
        "rainfall_1h_mm": data.get("rain", {}).get("1h", 0.0),
        "timestamp": datetime.utcfromtimestamp(data["dt"]).isoformat(),
    }


def get_rain_probability(location: str, api_key: str, hours_ahead: int = 6) -> float:
    """
    Get probability of rain in the next N hours using 3h forecast.

    Returns:
        Rain probability as float (0.0 to 1.0)
    """
    url = f"{OWM_BASE}/forecast"
    params = {"q": location, "appid": api_key, "units": "metric", "cnt": max(hours_ahead // 3, 1)}

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        logger.error(f"Forecast API error: {e}")
        return 0.0

    forecasts = data.get("list", [])
    if not forecasts:
        return 0.0

    rain_probs = [f.get("pop", 0.0) for f in forecasts]
    return max(rain_probs)


def get_solar_radiation_estimate(cloud_cover_pct: float, lat: float, day_of_year: int) -> float:
    """
    Estimate solar radiation (MJ/m²/day) from cloud cover.
    Uses simplified Angstrom equation.

    Args:
        cloud_cover_pct: Percentage cloud cover (0-100)
        lat: Latitude in degrees
        day_of_year: Julian day

    Returns:
        Estimated solar radiation in MJ/m²/day
    """
    import math
    phi = math.radians(lat)
    dr = 1 + 0.033 * math.cos(2 * math.pi * day_of_year / 365)
    delta = 0.409 * math.sin(2 * math.pi * day_of_year / 365 - 1.39)
    omega_s = math.acos(-math.tan(phi) * math.tan(delta))

    Ra = (24 * 60 / math.pi) * 0.0820 * dr * (
        omega_s * math.sin(phi) * math.sin(delta)
        + math.cos(phi) * math.cos(delta) * math.sin(omega_s)
    )

    # Angstrom: Rs = (as + bs * n/N) * Ra
    # Approximate sunshine fraction from cloud cover
    sunshine_fraction = max(0.0, 1.0 - (cloud_cover_pct / 100.0))
    as_coeff, bs_coeff = 0.25, 0.50
    Rs = (as_coeff + bs_coeff * sunshine_fraction) * Ra
    return Rs


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    API_KEY = os.getenv("OWM_API_KEY", "YOUR_API_KEY")
    LOCATION = "Warangal,IN"

    weather = get_current_weather(LOCATION, API_KEY)
    print("Current Weather:", weather)

    rain_prob = get_rain_probability(LOCATION, API_KEY, hours_ahead=6)
    print(f"Rain probability (next 6h): {rain_prob:.0%}")
