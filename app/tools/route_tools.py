"""
route_tools.py — Trip-planning helper functions for CommuteGenie.

Responsibilities:
- Geocode origin / destination using the existing Google Places client.
- Fetch route options for all relevant modes via the Directions API.
- Decide which real-time LTA / weather signals are needed (conditional).
- Collect only the relevant signals.
- Score routes and return a ranked recommendation payload.
"""

from typing import Any, Dict, List, Optional

from app.tools.google_maps_client import google_maps_client
from app.tools.transit_tools import (
    tool_nearest_bus_stops,
    tool_bus_arrival,
    tool_train_alerts,
    tool_traffic_incidents,
    tool_taxi_availability,
)
from app.tools.context_tools import get_weather_context, get_sg_time_context


# ---------------------------------------------------------------------------
# 1. Geocoding
# ---------------------------------------------------------------------------

def geocode_location(query: str) -> Dict[str, Any]:
    """
    Resolve a free-text location to lat/lon using the existing Places client.
    Returns {"matched": bool, "name": str, "latitude": float, "longitude": float, ...}
    """
    print(f"[Route] Geocoding: '{query}'")
    try:
        raw = google_maps_client.search_place(query)
        places = raw.get("places", [])

        if not places:
            return {"matched": False, "query": query, "error": "No places found."}

        top = places[0]
        loc = top.get("location", {}) or {}
        lat = loc.get("latitude")
        lon = loc.get("longitude")

        if lat is None or lon is None:
            return {"matched": False, "query": query, "error": "Place has no coordinates."}

        return {
            "matched": True,
            "query": query,
            "name": ((top.get("displayName") or {}).get("text")) or query,
            "latitude": float(lat),
            "longitude": float(lon),
            "address": top.get("formattedAddress", ""),
            "types": top.get("types", []),
        }

    except Exception as exc:
        return {"matched": False, "query": query, "error": str(exc)}


# ---------------------------------------------------------------------------
# 2. Route options
# ---------------------------------------------------------------------------

def get_route_options(
    origin: str,
    destination: str,
    modes: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Call Google Directions API for the requested modes (default: driving + transit).
    Returns dict keyed by mode with duration, distance, steps, and warnings.
    """
    modes = modes or ["driving", "transit"]
    print(f"[Route] Fetching directions for modes {modes}: {origin} → {destination}")
    try:
        return google_maps_client.get_directions(
            origin=origin,
            destination=destination,
            modes=modes,
        )
    except Exception as exc:
        return {"error": str(exc)}


# ---------------------------------------------------------------------------
# 3. Decide which real-time signals are needed
# ---------------------------------------------------------------------------

def decide_realtime_needs(route_results: Dict[str, Any]) -> Dict[str, bool]:
    """
    Inspect available route modes and decide which LTA / context signals to fetch.

    Logic:
    - driving present and no error        → check traffic incidents
    - transit present and no error        → check train alerts + nearest bus stops
    - transit has bus steps               → check bus arrivals at nearest stop
    - walking > 10 min in any step        → check weather
    - taxi mode requested                 → check taxi availability
    - any valid route                     → always check time context (cheap, local)
    """
    needs: Dict[str, bool] = {
        "traffic": False,
        "train_alerts": False,
        "bus_stops": False,
        "bus_arrivals": False,
        "taxi": False,
        "weather": False,
        "time": True,  # always — it is free (no HTTP)
    }

    for mode, data in route_results.items():
        if "error" in data:
            continue

        if mode == "driving":
            needs["traffic"] = True

        if mode == "taxi":
            needs["taxi"] = True
            needs["traffic"] = True

        if mode == "transit":
            needs["train_alerts"] = True
            needs["bus_stops"] = True
            steps = data.get("steps", [])
            for step in steps:
                vehicle = step.get("transit_vehicle", "")
                if vehicle in {"bus", "share_taxi"}:
                    needs["bus_arrivals"] = True
                # Walking > 10 min triggers weather check
                if step.get("mode") == "walking" and step.get("duration_mins", 0) > 10:
                    needs["weather"] = True

        if mode == "walking":
            duration = data.get("duration_mins", 0)
            if duration > 10:
                needs["weather"] = True

    return needs


# ---------------------------------------------------------------------------
# 4. Fetch only the needed real-time signals
# ---------------------------------------------------------------------------

def fetch_realtime_context(
    needs: Dict[str, bool],
    origin_coords: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Call only the tools flagged as needed.  Returns a dict of signal_name → data.
    origin_coords, if provided, is used to locate nearby bus stops.
    """
    ctx: Dict[str, Any] = {}

    if needs.get("time"):
        print("[Route] Fetching time context")
        ctx["time"] = get_sg_time_context()

    if needs.get("weather"):
        print("[Route] Fetching weather context")
        ctx["weather"] = get_weather_context()

    if needs.get("traffic"):
        print("[Route] Fetching traffic incidents")
        ctx["traffic"] = tool_traffic_incidents()

    if needs.get("train_alerts"):
        print("[Route] Fetching train alerts")
        ctx["train_alerts"] = tool_train_alerts()

    if needs.get("taxi"):
        print("[Route] Fetching taxi availability")
        ctx["taxi"] = tool_taxi_availability()

    if needs.get("bus_stops") and origin_coords and origin_coords.get("matched"):
        print("[Route] Fetching nearest bus stops near origin")
        loc = {
            "latitude": origin_coords["latitude"],
            "longitude": origin_coords["longitude"],
            "name": origin_coords.get("name", "origin"),
        }
        nearest = tool_nearest_bus_stops(max_results=3, current_location=loc)
        ctx["nearest_bus_stops"] = nearest

        if needs.get("bus_arrivals"):
            # Fetch arrivals for the closest stop
            stops = nearest.get("results", [])
            if stops:
                top_stop_code = stops[0].get("BusStopCode")
                if top_stop_code:
                    print(f"[Route] Fetching bus arrivals for stop {top_stop_code}")
                    ctx["bus_arrivals_at_origin"] = tool_bus_arrival(top_stop_code)

    return ctx


# ---------------------------------------------------------------------------
# 5. Scoring
# ---------------------------------------------------------------------------

# Penalty weights (applied as additive minutes to the raw duration)
_PENALTY = {
    "traffic_heavy": 15,
    "train_disruption": 20,
    "bus_wait_long": 5,
    "weather_high_impact": 10,
    "weather_moderate_impact": 5,
    "extra_transfer": 8,
}


def _weather_penalty(realtime: Dict[str, Any]) -> float:
    impact = realtime.get("weather", {}).get("impact", "unknown")
    if impact == "high":
        return _PENALTY["weather_high_impact"]
    if impact == "moderate":
        return _PENALTY["weather_moderate_impact"]
    return 0.0


def _traffic_penalty(realtime: Dict[str, Any]) -> float:
    incidents = realtime.get("traffic", {})
    count = incidents.get("count", 0)
    if count >= 5:
        return _PENALTY["traffic_heavy"]
    if count >= 2:
        return round(_PENALTY["traffic_heavy"] * 0.5, 1)
    return 0.0


def _train_penalty(realtime: Dict[str, Any]) -> float:
    alerts = realtime.get("train_alerts", {})
    raw = alerts.get("raw", {})
    # LTA TrainServiceAlerts: status 1 = normal, anything else = disruption
    status = raw.get("Status", 1) if isinstance(raw, dict) else 1
    if status != 1:
        return _PENALTY["train_disruption"]
    return 0.0


def _bus_wait_penalty(realtime: Dict[str, Any]) -> float:
    arrivals = realtime.get("bus_arrivals_at_origin", {})
    services = arrivals.get("services", [])
    if not services:
        return 0.0
    min_wait = min(
        (s.get("next_bus_mins") or 99) for s in services
    )
    if min_wait > 15:
        return _PENALTY["bus_wait_long"]
    return 0.0


def _transfer_penalty(route: Dict[str, Any]) -> float:
    transfers = route.get("num_transfers", 0)
    return transfers * _PENALTY["extra_transfer"]


def score_routes(
    route_results: Dict[str, Any],
    realtime: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Score each available route and return them sorted best → worst.

    Each entry:
      mode, raw_duration_mins, penalty_mins, effective_mins,
      score_breakdown, warnings
    """
    scored: List[Dict[str, Any]] = []

    weather_pen = _weather_penalty(realtime)
    traffic_pen = _traffic_penalty(realtime)
    train_pen = _train_penalty(realtime)
    bus_wait_pen = _bus_wait_penalty(realtime)

    for mode, data in route_results.items():
        if "error" in data:
            continue

        raw = data.get("duration_mins", 9999)
        penalty = 0.0
        breakdown: Dict[str, float] = {}

        if mode in {"driving", "taxi"}:
            if traffic_pen:
                penalty += traffic_pen
                breakdown["traffic_incidents"] = traffic_pen
            if weather_pen:
                penalty += weather_pen
                breakdown["weather"] = weather_pen

        if mode == "transit":
            if train_pen:
                penalty += train_pen
                breakdown["train_disruption"] = train_pen
            if bus_wait_pen:
                penalty += bus_wait_pen
                breakdown["bus_wait"] = bus_wait_pen
            tp = _transfer_penalty(data)
            if tp:
                penalty += tp
                breakdown["extra_transfers"] = tp
            if weather_pen:
                # Only penalise transit weather if there are long walking steps
                has_long_walk = any(
                    s.get("mode") == "walking" and s.get("duration_mins", 0) > 10
                    for s in data.get("steps", [])
                )
                if has_long_walk:
                    penalty += weather_pen
                    breakdown["weather_walk"] = weather_pen

        if mode == "walking":
            if weather_pen:
                penalty += weather_pen * 2
                breakdown["weather_walking"] = weather_pen * 2

        effective = round(raw + penalty, 1)
        scored.append({
            "mode": mode,
            "raw_duration_mins": raw,
            "penalty_mins": round(penalty, 1),
            "effective_mins": effective,
            "distance_km": data.get("distance_km", 0),
            "num_transfers": data.get("num_transfers", 0),
            "summary": data.get("summary", ""),
            "steps": data.get("steps", []),
            "warnings": data.get("warnings", []),
            "score_breakdown": breakdown,
        })

    scored.sort(key=lambda x: x["effective_mins"])
    return scored


# ---------------------------------------------------------------------------
# 6. Build the final trip result payload
# ---------------------------------------------------------------------------

def build_trip_result(
    origin_query: str,
    destination_query: str,
    origin_geo: Dict[str, Any],
    destination_geo: Dict[str, Any],
    route_results: Dict[str, Any],
    realtime: Dict[str, Any],
    scored_routes: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Assemble the full trip result that will be stored in state['trip_result']
    and handed to the manager writer.
    """
    best = scored_routes[0] if scored_routes else None
    backup = scored_routes[1] if len(scored_routes) > 1 else None

    warnings: List[str] = []
    if realtime.get("train_alerts", {}).get("raw", {}).get("Status", 1) != 1:
        warnings.append("MRT service disruption reported.")
    if (realtime.get("traffic", {}).get("count", 0) or 0) >= 3:
        warnings.append("Multiple traffic incidents on roads.")
    impact = realtime.get("weather", {}).get("impact", "unknown")
    if impact in {"high", "moderate"}:
        warnings.append(f"Weather impact: {impact} — {realtime['weather'].get('condition','')}")

    return {
        "origin": {
            "query": origin_query,
            "resolved": origin_geo.get("name", origin_query),
            "address": origin_geo.get("address", ""),
            "matched": origin_geo.get("matched", False),
        },
        "destination": {
            "query": destination_query,
            "resolved": destination_geo.get("name", destination_query),
            "address": destination_geo.get("address", ""),
            "matched": destination_geo.get("matched", False),
        },
        "best_option": best,
        "backup_option": backup,
        "all_options": scored_routes,
        "realtime_checked": list(realtime.keys()),
        "realtime": realtime,
        "warnings": warnings,
    }
