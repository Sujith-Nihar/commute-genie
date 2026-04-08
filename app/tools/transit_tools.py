from datetime import datetime
from typing import Any, Dict, List, Optional
import pytz
import math
import requests
from app.tools.context_tools import get_current_location_context
from app.tools.google_maps_client import google_maps_client

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
            "error": "LTA client is not initialized. Check LTA_ACCOUNT_KEY in your environment."
        }

    params = {"BusStopCode": bus_stop_code}
    if service_no:
        params["ServiceNo"] = service_no

    raw = lta_client.get("v3/BusArrival", params=params)

    if "error" in raw:
        return {
            "error": raw["error"],
            "bus_stop_code": bus_stop_code,
            "service_no": service_no,
            "raw": raw,
        }

    services = []
    for svc in raw.get("Services", [])[:5]:
        services.append(
            {
                "service_no": svc.get("ServiceNo"),
                "operator": svc.get("Operator"),
                "next_bus_mins": _minutes_until(
                    svc.get("NextBus", {}).get("EstimatedArrival")
                ),
                "next_bus_2_mins": _minutes_until(
                    svc.get("NextBus2", {}).get("EstimatedArrival")
                ),
                "next_bus_3_mins": _minutes_until(
                    svc.get("NextBus3", {}).get("EstimatedArrival")
                ),
            }
        )

    return {
        "mock": False,
        "bus_stop_code": bus_stop_code,
        "service_no": service_no,
        "services": services,
        "raw_keys": list(raw.keys()),
    }


def tool_bus_stops_search(query: str, max_results: int = 5) -> Dict[str, Any]:
    cached = cache.get("busstops_all")

    if cached is None:
        if not lta_client:
            return {
                "error": "LTA client is not initialized. Check LTA_ACCOUNT_KEY in your environment."
            }

        cached = lta_client.get_paged("BusStops")
        cache.set("busstops_all", cached, ttl_s=6 * 3600)

    q = query.lower().strip()
    q_words = [word for word in q.split() if word]
    hits: List[Dict[str, Any]] = []

    for row in cached:
        description = row.get("Description", "")
        road_name = row.get("RoadName", "")
        text = f"{description} {road_name}".lower()

        if q and q in text:
            hits.append(
                {
                    "BusStopCode": row.get("BusStopCode"),
                    "RoadName": road_name,
                    "Description": description,
                }
            )
            continue

        if q_words and all(word in text for word in q_words):
            hits.append(
                {
                    "BusStopCode": row.get("BusStopCode"),
                    "RoadName": road_name,
                    "Description": description,
                }
            )

        if len(hits) >= max_results:
            break

    return {
        "query": query,
        "count": len(hits),
        "results": hits,
    }


def tool_traffic_incidents() -> Dict[str, Any]:
    cached = cache.get("traffic_incidents")
    if cached is not None:
        return cached

    if not lta_client:
        return {
            "error": "LTA client is not initialized. Check LTA_ACCOUNT_KEY in your environment."
        }

    raw = lta_client.get("TrafficIncidents")

    if "error" in raw:
        return raw

    rows = raw.get("value", [])
    result = {
        "mock": False,
        "count": len(rows),
        "top_incidents": rows[:5],
    }
    cache.set("traffic_incidents", result, ttl_s=30)
    return result


def tool_train_alerts() -> Dict[str, Any]:
    cached = cache.get("train_alerts")
    if cached is not None:
        return cached

    if not lta_client:
        return {
            "error": "LTA client is not initialized. Check LTA_ACCOUNT_KEY in your environment."
        }

    raw = lta_client.get("TrainServiceAlerts")

    if "error" in raw:
        return raw

    result = {
        "mock": False,
        "raw": raw,
    }
    cache.set("train_alerts", result, ttl_s=30)
    return result


def tool_taxi_availability() -> Dict[str, Any]:
    cached = cache.get("taxi_availability")
    if cached is not None:
        return cached

    if not lta_client:
        return {
            "error": "LTA client is not initialized. Check LTA_ACCOUNT_KEY in your environment."
        }

    raw = lta_client.get("Taxi-Availability")

    if "error" in raw:
        return raw

    rows = raw.get("value", [])
    result = {
        "mock": False,
        "count": len(rows),
        "top_taxis": rows[:5],
    }
    cache.set("taxi_availability", result, ttl_s=30)
    return result

def _to_float(value: Any) -> Optional[float]:
    try:
        if value in (None, "", " "):
            return None
        return float(value)
    except Exception:
        return None


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return r * c


def _resolve_location(current_location: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    loc = current_location or get_current_location_context()
    lat = _to_float(loc.get("latitude"))
    lon = _to_float(loc.get("longitude"))

    if lat is None or lon is None:
        raise ValueError("Current location must include valid latitude and longitude.")

    return {
        "name": loc.get("name", "current location"),
        "latitude": lat,
        "longitude": lon,
        "postal_code": loc.get("postal_code"),
        "source": loc.get("source", "unknown"),
    }


def _get_all_bus_stops() -> List[Dict[str, Any]]:
    cached = cache.get("busstops_all")
    if cached is not None:
        return cached

    if not lta_client:
        raise RuntimeError("LTA client is not initialized. Check LTA_ACCOUNT_KEY in your environment.")

    cached = lta_client.get_paged("BusStops")
    cache.set("busstops_all", cached, ttl_s=6 * 3600)
    return cached
def tool_nearest_bus_stops(
    max_results: int = 5,
    current_location: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    try:
        loc = _resolve_location(current_location)
        rows = _get_all_bus_stops()
    except Exception as e:
        return {"error": str(e)}

    scored: List[Dict[str, Any]] = []

    for row in rows:
        lat = _to_float(row.get("Latitude"))
        lon = _to_float(row.get("Longitude"))
        if lat is None or lon is None:
            continue

        distance_km = _haversine_km(
            loc["latitude"], loc["longitude"], lat, lon
        )

        scored.append(
            {
                "BusStopCode": row.get("BusStopCode"),
                "RoadName": row.get("RoadName"),
                "Description": row.get("Description"),
                "Latitude": lat,
                "Longitude": lon,
                "distance_km": round(distance_km, 3),
            }
        )

    scored.sort(key=lambda x: x["distance_km"])

    return {
        "current_location": loc,
        "count": min(len(scored), max_results),
        "results": scored[:max_results],
    }
def _get_all_ev_charging_points() -> List[Dict[str, Any]]:
    cached = cache.get("ev_charging_points_all")
    if cached is not None:
        return cached

    if not lta_client:
        raise RuntimeError("LTA client is not initialized. Check LTA_ACCOUNT_KEY in your environment.")

    meta = lta_client.get("EVCBatch")
    if "error" in meta:
        raise RuntimeError(meta["error"])

    link = meta.get("Link")
    if not link and isinstance(meta.get("value"), list) and meta["value"]:
        link = meta["value"][0].get("Link")

    if not link:
        raise RuntimeError("Could not find EV batch download link from EVCBatch response.")

    resp = requests.get(link, timeout=30)
    resp.raise_for_status()
    payload = resp.json()

    if isinstance(payload, list):
        rows = payload
    elif isinstance(payload, dict):
        rows = (
            payload.get("value")
            or payload.get("data")
            or payload.get("items")
            or []
        )
    else:
        rows = []

    cache.set("ev_charging_points_all", rows, ttl_s=300)
    return rows


def tool_nearest_ev_charging_points(
    max_results: int = 5,
    current_location: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    try:
        loc = _resolve_location(current_location)
        rows = _get_all_ev_charging_points()
    except Exception as e:
        return {"error": str(e)}

    scored: List[Dict[str, Any]] = []

    for row in rows:
        lat = _to_float(row.get("latitude") or row.get("Latitude"))
        lon = _to_float(
            row.get("longtitude") or row.get("longitude") or row.get("Longitude")
        )
        if lat is None or lon is None:
            continue

        charging_points = row.get("chargingPoints", [])
        available_count = 0
        if isinstance(charging_points, list):
            available_count = sum(
                1 for cp in charging_points if str(cp.get("status")) == "1"
            )

        distance_km = _haversine_km(
            loc["latitude"], loc["longitude"], lat, lon
        )

        scored.append(
            {
                "name": row.get("name"),
                "address": row.get("address"),
                "latitude": lat,
                "longitude": lon,
                "location_id": row.get("locationId"),
                "station_status": row.get("status"),
                "available_points": available_count,
                "distance_km": round(distance_km, 3),
            }
        )

    scored.sort(key=lambda x: x["distance_km"])

    return {
        "current_location": loc,
        "count": min(len(scored), max_results),
        "results": scored[:max_results],
    }
def tool_resolve_location_query(location_query: str) -> Dict[str, Any]:
    q = location_query.strip()
    if not q:
        return {"matched": False, "error": "Empty location query."}

    try:
        raw = google_maps_client.search_place(q)
        places = raw.get("places", [])

        if not places:
            return {
                "query": q,
                "matched": False,
                "error": f"No Google Places results found for '{q}'.",
                "raw": raw,
            }

        top = places[0]
        location = top.get("location", {}) or {}
        lat = _to_float(location.get("latitude"))
        lon = _to_float(location.get("longitude"))

        if lat is None or lon is None:
            return {
                "query": q,
                "matched": False,
                "error": "Resolved place did not include usable coordinates.",
                "raw_top_result": top,
            }

        return {
            "query": q,
            "matched": True,
            "location": {
                "name": ((top.get("displayName") or {}).get("text")) or q,
                "latitude": lat,
                "longitude": lon,
                "postal_code": None,
                "address": top.get("formattedAddress"),
                "types": top.get("types", []),
                "source": "google_places_text_search",
            },
            "raw_top_result": top,
        }

    except Exception as e:
        return {
            "query": q,
            "matched": False,
            "error": f"Google Maps search failed: {e}",
        }