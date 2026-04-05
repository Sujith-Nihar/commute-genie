from datetime import datetime
from typing import Any, Dict, List, Optional
import pytz

from app.tools.lta_client import lta_client

SG_TZ = pytz.timezone("Asia/Singapore")


class TTLCache:
    def __init__(self):
        self._store: Dict[str, Any] = {}

    def get(self, key: str):
        import time
        item = self._store.get(key)
        if not item:
            return None
        value, expires_at = item
        if time.time() > expires_at:
            self._store.pop(key, None)
            return None
        return value

    def set(self, key: str, value: Any, ttl_s: int):
        import time
        self._store[key] = (value, time.time() + ttl_s)


cache = TTLCache()


def _minutes_until(arrival_iso: Optional[str]) -> Optional[int]:
    if not arrival_iso:
        return None
    try:
        arrival_dt = datetime.fromisoformat(arrival_iso.replace("Z", "+00:00"))
        now = datetime.now(arrival_dt.tzinfo)
        delta = arrival_dt - now
        return max(0, int(delta.total_seconds() // 60))
    except Exception:
        return None


def tool_bus_arrival(bus_stop_code: str, service_no: Optional[str] = None) -> Dict[str, Any]:
    if not lta_client:
        return {
            "mock": True,
            "bus_stop_code": bus_stop_code,
            "service_no": service_no or "12",
            "services": [
                {
                    "service_no": service_no or "12",
                    "next_bus_mins": 4
                }
            ]
        }

    params = {"BusStopCode": bus_stop_code}
    if service_no:
        params["ServiceNo"] = service_no

    raw = lta_client.get("v3/BusArrival", params=params)
    services = []

    for svc in raw.get("Services", [])[:5]:
        services.append({
            "service_no": svc.get("ServiceNo"),
            "next_bus_mins": _minutes_until(svc.get("NextBus", {}).get("EstimatedArrival")),
            "next_bus_2_mins": _minutes_until(svc.get("NextBus2", {}).get("EstimatedArrival")),
            "next_bus_3_mins": _minutes_until(svc.get("NextBus3", {}).get("EstimatedArrival")),
        })

    return {
        "mock": False,
        "bus_stop_code": bus_stop_code,
        "service_no": service_no,
        "services": services,
    }


def tool_bus_stops_search(query: str, max_results: int = 5) -> Dict[str, Any]:
    cached = cache.get("busstops_all")
    if cached is None:
        if lta_client:
            cached = lta_client.get_paged("BusStops")
        else:
            cached = []
        cache.set("busstops_all", cached, ttl_s=6 * 3600)

    q = query.lower().strip()
    hits: List[Dict[str, Any]] = []

    for row in cached:
        text = f"{row.get('Description', '')} {row.get('RoadName', '')}".lower()
        if q in text:
            hits.append({
                "BusStopCode": row.get("BusStopCode"),
                "RoadName": row.get("RoadName"),
                "Description": row.get("Description"),
            })
        if len(hits) >= max_results:
            break

    if not lta_client and not hits:
        hits = [{
            "BusStopCode": "83139",
            "RoadName": "Orchard Rd",
            "Description": "Lucky Plaza"
        }]

    return {
        "query": query,
        "count": len(hits),
        "results": hits
    }


def tool_traffic_incidents() -> Dict[str, Any]:
    cached = cache.get("traffic_incidents")
    if cached is not None:
        return cached

    if not lta_client:
        result = {
            "mock": True,
            "count": 1,
            "top_incidents": [{"Type": "Accident", "Message": "Simulated incident on PIE"}]
        }
        cache.set("traffic_incidents", result, ttl_s=30)
        return result

    raw = lta_client.get("TrafficIncidents")
    rows = raw.get("value", [])

    result = {
        "mock": False,
        "count": len(rows),
        "top_incidents": rows[:5]
    }
    cache.set("traffic_incidents", result, ttl_s=30)
    return result


def tool_train_alerts() -> Dict[str, Any]:
    cached = cache.get("train_alerts")
    if cached is not None:
        return cached

    if not lta_client:
        result = {
            "mock": True,
            "count": 1,
            "alerts": [{"Status": "No major disruption", "Line": "EWL"}]
        }
        cache.set("train_alerts", result, ttl_s=30)
        return result

    raw = lta_client.get("TrainServiceAlerts")
    result = {
        "mock": False,
        "raw": raw
    }
    cache.set("train_alerts", result, ttl_s=30)
    return result


def tool_taxi_availability() -> Dict[str, Any]:
    cached = cache.get("taxi_availability")
    if cached is not None:
        return cached

    if not lta_client:
        result = {
            "mock": True,
            "count": 2450
        }
        cache.set("taxi_availability", result, ttl_s=30)
        return result

    raw = lta_client.get("Taxi-Availability")
    rows = raw.get("value", [])
    result = {
        "mock": False,
        "count": len(rows)
    }
    cache.set("taxi_availability", result, ttl_s=30)
    return result