from datetime import datetime
from typing import Any, Dict, Optional

import holidays
import pytz
import requests

from app.config import settings

SG_TZ = pytz.timezone("Asia/Singapore")
SG_HOLIDAYS = holidays.Singapore()

# Dummy current location for local development / demo
# Lucky Plaza area, Orchard Road
"""
CURRENT_LOCATION = {
    "name": "Lucky Plaza (dummy current location)",
    "latitude": 1.3044,
    "longitude": 103.8331,
    "postal_code": "238863",
    "source": "dummy",
}
"""
CURRENT_LOCATION = {
    "name": "Queensway Shopping Centre (dummy current location)",
    "latitude": 1.2876,
    "longitude": 103.8034,
    "postal_code": "149053",
    "source": "dummy",
}

def get_sg_time_context() -> Dict[str, Any]:
    now = datetime.now(SG_TZ)
    hour = now.hour

    return {
        "timestamp": now.isoformat(),
        "hour": hour,
        "weekday": now.strftime("%A"),
        "is_weekend": now.weekday() >= 5,
        "is_rush_hour": (7 <= hour <= 10) or (17 <= hour <= 20),
    }


def get_sg_holiday_context(date_obj: Optional[datetime] = None) -> Dict[str, Any]:
    d = (date_obj or datetime.now(SG_TZ)).date()
    holiday_name = SG_HOLIDAYS.get(d)

    return {
        "date": str(d),
        "is_public_holiday": holiday_name is not None,
        "holiday_name": holiday_name,
    }


def infer_weather_impact(condition: str, description: str) -> str:
    text = f"{condition} {description}".lower()

    if "thunderstorm" in text:
        return "high"
    if "rain" in text or "drizzle" in text:
        return "moderate"
    if "cloud" in text:
        return "low"
    if "clear" in text:
        return "minimal"
    return "unknown"


def get_weather_context():
    if not settings.OPENWEATHER_API_KEY:
        return {
            "condition": "unknown",
            "impact": "unknown",
            "note": "API key not set",
        }

    url = "https://api.weatherapi.com/v1/current.json"

    params = {
        "key": settings.OPENWEATHER_API_KEY,   # reuse same env variable
        "q": "Singapore",
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        current = data["current"]

        condition = current["condition"]["text"]

        return {
            "condition": condition,
            "temperature_c": current["temp_c"],
            "humidity": current["humidity"],
            "wind_kph": current["wind_kph"],
            "impact": infer_weather_impact(condition, condition),
            "note": "WeatherAPI working successfully",
        }

    except Exception as e:
        return {
            "condition": "unknown",
            "impact": "unknown",
            "note": str(e),
        }
    
def get_current_location_context() -> Dict[str, Any]:
    return dict(CURRENT_LOCATION)
