from datetime import datetime
from typing import Any, Dict, Optional
import pytz
import holidays

SG_TZ = pytz.timezone("Asia/Singapore")
SG_HOLIDAYS = holidays.Singapore()


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


def get_mock_weather_context() -> Dict[str, Any]:
    """
    Your notebook mentioned weather as a constraint.
    Since LTA DataMall does not provide weather directly, keep this lightweight for now.
    You can later replace this with NEA or OpenWeather.
    """
    return {
        "condition": "unknown",
        "impact": "unknown",
        "note": "Weather integration not yet connected; using placeholder context."
    }