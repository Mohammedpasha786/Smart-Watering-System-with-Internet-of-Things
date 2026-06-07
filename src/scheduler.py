"""
scheduler.py
Main orchestration loop for the Smart Watering System.
Runs every N minutes: fetches data, computes ET, makes prediction, triggers action.
"""

import os
import time
import logging
import yaml
from datetime import datetime

from data_fetcher import fetch_latest_reading, write_to_channel
from weather_api import get_current_weather, get_rain_probability, get_solar_radiation_estimate
from et_calculator import SensorData, compute_et0, compute_crop_et, irrigation_deficit
from irrigation_model import predict, engineer_features
from notifier import send_email_alert

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/smart_watering.log"),
    ],
)
logger = logging.getLogger(__name__)


def load_config(path: str = "../../config/config.yaml") -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def run_irrigation_cycle(config: dict):
    """Single decision cycle: sense → analyze → act."""
    ts_cfg = config["thingspeak"]
    weather_cfg = config["weather"]
    irr_cfg = config["irrigation"]
    crop_cfg = config["crop"]

    logger.info("── Starting irrigation decision cycle ────────────────")

    # 1. Fetch latest sensor data from ThingSpeak
    reading = fetch_latest_reading(ts_cfg["channel_id"], ts_cfg["read_api_key"])
    if not reading or reading.get("soil_moisture_pct") is None:
        logger.warning("Sensor data unavailable. Skipping cycle.")
        return

    logger.info(f"Sensor data: {reading}")

    # 2. Fetch weather data
    weather = get_current_weather(weather_cfg["location"], weather_cfg["api_key"])
    rain_prob = get_rain_probability(weather_cfg["location"], weather_cfg["api_key"], hours_ahead=6)

    logger.info(f"Weather: {weather.get('description', 'N/A')} | Rain prob 6h: {rain_prob:.0%}")

    # 3. Estimate ET₀
    doy = datetime.utcnow().timetuple().tm_yday
    cloud_cover = weather.get("cloud_cover_pct", 30)
    Rs = get_solar_radiation_estimate(cloud_cover, lat=17.98, day_of_year=doy)

    sensor_data = SensorData(
        temperature_c=reading.get("temperature_c", weather.get("temperature_c", 28)),
        humidity_pct=reading.get("humidity_pct", weather.get("humidity_pct", 60)),
        wind_speed_ms=weather.get("wind_speed_ms", 1.5),
        solar_radiation=Rs,
        elevation_m=260.0,
        latitude_deg=17.98,
    )
    et0 = compute_et0(sensor_data, day_of_year=doy)
    etc = compute_crop_et(et0, crop_cfg["type"], crop_cfg["growth_stage"])
    deficit = irrigation_deficit(etc, rainfall_mm=reading.get("rainfall_1h_mm", 0.0) * 24)

    logger.info(f"ET₀={et0:.2f} mm/day | ETc={etc:.2f} mm/day | Deficit={deficit:.2f} mm/day")

    # 4. ML prediction
    features = {
        "soil_moisture_pct": reading.get("soil_moisture_pct", 50),
        "temperature_c": reading.get("temperature_c", 28),
        "humidity_pct": reading.get("humidity_pct", 60),
        "light_lux": reading.get("light_lux", 500),
        "ph_value": reading.get("ph_value", 7.0),
        "et0_mm_day": et0,
        "rain_prob_6h": rain_prob,
        "hour_of_day": datetime.utcnow().hour,
        "day_of_week": datetime.utcnow().weekday(),
        "growth_stage_encoded": {"initial": 0, "vegetative": 1, "flowering": 2, "ripening": 3}.get(
            crop_cfg.get("growth_stage", "vegetative"), 1
        ),
    }

    prediction = predict(features)
    logger.info(f"ML Prediction: {'IRRIGATE' if prediction['irrigate'] else 'No action'} "
                f"(confidence={prediction['confidence']:.1%})")

    # 5. Decision: irrigate if ML says yes OR deficit is critical
    should_irrigate = prediction["irrigate"] or (deficit > 3.0 and rain_prob < 0.3)

    if should_irrigate:
        pump_duration = min(
            irr_cfg["pump_duration_seconds"] * (deficit / 3.0),
            irr_cfg.get("max_pump_duration_seconds", 120),
        )
        logger.info(f"ACTION: Triggering pump for {pump_duration:.0f} seconds")

        # Write pump ON flag to ThingSpeak (ESP32 polls this field)
        write_to_channel(
            ts_cfg["channel_id"],
            ts_cfg["write_api_key"],
            {"field8": 1},  # Field 8 = remote pump command
        )

        # Send notification
        msg = (
            f"🌱 Smart Watering Alert\n"
            f"Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n"
            f"Soil Moisture: {reading.get('soil_moisture_pct', 'N/A'):.1f}%\n"
            f"ET₀: {et0:.2f} mm/day | Deficit: {deficit:.2f} mm/day\n"
            f"Rain probability (6h): {rain_prob:.0%}\n"
            f"ML Confidence: {prediction['confidence']:.1%}\n"
            f"Action: Pump activated for {pump_duration:.0f}s"
        )
        send_email_alert(
            to_email=config["notifications"]["email"],
            subject="Smart Watering: Irrigation Triggered",
            body=msg,
            smtp_config=config["notifications"],
        )
    else:
        logger.info("No irrigation needed. Conditions OK.")

    logger.info("── Cycle complete ─────────────────────────────────────\n")


def main():
    os.makedirs("logs", exist_ok=True)
    config = load_config()
    interval_sec = config["irrigation"]["check_interval_minutes"] * 60

    logger.info("Smart Watering System Scheduler started.")
    logger.info(f"Check interval: {config['irrigation']['check_interval_minutes']} minutes")

    while True:
        try:
            run_irrigation_cycle(config)
        except Exception as e:
            logger.error(f"Cycle error: {e}", exc_info=True)

        logger.info(f"Next check in {interval_sec // 60} minutes...")
        time.sleep(interval_sec)


if __name__ == "__main__":
    main()
