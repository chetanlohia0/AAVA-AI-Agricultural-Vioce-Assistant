"""
services/weather_service.py

Wraps OpenWeatherMap's current-conditions and forecast endpoints so
farmers can ask "will it rain tomorrow?" alongside price queries.
Falls back to a fixed demo response when no API key is configured,
so the rest of the system (NLU, voice response) can be developed and
demoed without needing live network access or paid API credits.
"""

import os
import requests

DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
OPENWEATHER_BASE_URL = os.getenv("OPENWEATHER_BASE_URL", "https://api.openweathermap.org/data/2.5")

_DEMO_WEATHER = {
    "condition": "light rain expected",
    "temp_c": 28,
    "humidity_pct": 76,
    "rain_probability_pct": 65,
}


def get_weather(location: str) -> dict:
    if DEMO_MODE or not OPENWEATHER_API_KEY:
        return {"location": location or "your area", **_DEMO_WEATHER, "source": "demo"}
    return _fetch_live_weather(location)


def _fetch_live_weather(location: str) -> dict:
    params = {"q": f"{location},IN", "appid": OPENWEATHER_API_KEY, "units": "metric"}
    response = requests.get(f"{OPENWEATHER_BASE_URL}/weather", params=params, timeout=4)
    response.raise_for_status()
    data = response.json()
    return {
        "location": location,
        "condition": data["weather"][0]["description"],
        "temp_c": data["main"]["temp"],
        "humidity_pct": data["main"]["humidity"],
        "rain_probability_pct": None,  # requires the /forecast endpoint for probability of precipitation
        "source": "live",
    }
