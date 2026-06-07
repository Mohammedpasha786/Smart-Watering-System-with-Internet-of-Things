"""
data_fetcher.py
Fetch sensor data from ThingSpeak IoT platform.
"""

import os
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

THINGSPEAK_BASE = "https://api.thingspeak.com"

FIELD_MAP = {
    "field1": "soil_moisture_pct",
    "field2": "temperature_c",
    "field3": "humidity_pct",
    "field4": "light_lux",
    "field5": "ph_value",
    "field6": "pump_status",
}


def fetch_channel_data(
    channel_id: str,
    read_api_key: str,
    results: int = 100,
    days: Optional[int] = None,
) -> pd.DataFrame:
    """
    Fetch recent feed data from a ThingSpeak channel.

    Args:
        channel_id: ThingSpeak channel ID
        read_api_key: Channel read API key
        results: Number of data points (max 8000)
        days: If set, fetch last N days instead of fixed results

    Returns:
        DataFrame with parsed sensor columns
    """
    url = f"{THINGSPEAK_BASE}/channels/{channel_id}/feeds.json"
    params = {"api_key": read_api_key, "results": results}

    if days:
        start = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
        params["start"] = start
        params.pop("results", None)

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        logger.error(f"ThingSpeak fetch failed: {e}")
        return pd.DataFrame()

    feeds = data.get("feeds", [])
    if not feeds:
        logger.warning("No data returned from ThingSpeak")
        return pd.DataFrame()

    df = pd.DataFrame(feeds)
    df["created_at"] = pd.to_datetime(df["created_at"])
    df = df.rename(columns=FIELD_MAP)
    df = df.set_index("created_at")

    for col in FIELD_MAP.values():
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    logger.info(f"Fetched {len(df)} records from ThingSpeak channel {channel_id}")
    return df


def fetch_latest_reading(channel_id: str, read_api_key: str) -> dict:
    """
    Fetch only the most recent sensor reading.

    Returns:
        dict with latest sensor values
    """
    url = f"{THINGSPEAK_BASE}/channels/{channel_id}/feeds/last.json"
    params = {"api_key": read_api_key}

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        raw = response.json()
    except requests.RequestException as e:
        logger.error(f"Latest reading fetch failed: {e}")
        return {}

    reading = {"timestamp": raw.get("created_at")}
    for field, name in FIELD_MAP.items():
        val = raw.get(field)
        reading[name] = float(val) if val is not None else None

    return reading


def write_to_channel(
    channel_id: str,
    write_api_key: str,
    fields: dict,
) -> bool:
    """
    Write data to a ThingSpeak channel (e.g., from Python trigger).

    Args:
        fields: dict like {"field1": value, "field6": 1}

    Returns:
        True if successful
    """
    url = f"{THINGSPEAK_BASE}/update.json"
    payload = {"api_key": write_api_key, **fields}

    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        entry_id = response.json()
        if entry_id == 0:
            logger.warning("ThingSpeak write returned 0 — rate limited or no data change")
            return False
        logger.info(f"ThingSpeak write OK. Entry ID: {entry_id}")
        return True
    except requests.RequestException as e:
        logger.error(f"ThingSpeak write failed: {e}")
        return False


if __name__ == "__main__":
    CHANNEL_ID = os.getenv("THINGSPEAK_CHANNEL_ID", "YOUR_CHANNEL_ID")
    READ_KEY = os.getenv("THINGSPEAK_READ_API_KEY", "YOUR_READ_KEY")

    latest = fetch_latest_reading(CHANNEL_ID, READ_KEY)
    print("Latest Reading:", latest)

    df = fetch_channel_data(CHANNEL_ID, READ_KEY, results=50)
    if not df.empty:
        print(df.tail(5).to_string())
