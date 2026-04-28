import re
import requests
from typing import Any, Dict, List, Optional

from app.config import settings

GOOGLE_PLACES_BASE_URL = "https://places.googleapis.com/v1"
GOOGLE_DIRECTIONS_BASE_URL = "https://maps.googleapis.com/maps/api/directions/json"

# Modes recognised by the Directions API
_DIRECTIONS_MODES = {"driving", "walking", "bicycling", "transit"}


class GoogleMapsClient:
    def __init__(self, api_key: Optional[str], timeout_s: int = 20):
        self.api_key = api_key
        self.timeout_s = timeout_s
        self.session = requests.Session()

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def _places_headers(self) -> Dict[str, str]:
        return {
            "X-Goog-Api-Key": self.api_key or "",
            "X-Goog-FieldMask": ",".join(
                [
                    "places.id",
                    "places.displayName",
                    "places.formattedAddress",
                    "places.location",
                    "places.types",
                ]
            ),
            "Content-Type": "application/json",
        }

    def search_place(self, query: str) -> Dict[str, Any]:
        if not self.is_configured():
            raise RuntimeError("GOOGLE_MAPS_API_KEY is missing.")

        url = f"{GOOGLE_PLACES_BASE_URL}/places:searchText"
        body = {
            "textQuery": f"{query}, Singapore",
            "regionCode": "SG",
            "languageCode": "en",
            "maxResultCount": 5,
            "locationBias": {
                "rectangle": {
                    "low": {"latitude": 1.1300, "longitude": 103.6000},
                    "high": {"latitude": 1.4700, "longitude": 104.1000},
                }
            },
        }

        response = self.session.post(
            url,
            headers=self._places_headers(),
            json=body,
            timeout=self.timeout_s,
        )

        if not response.ok:
            raise RuntimeError(
                f"Google Places error {response.status_code}: {response.text}"
            )

        return response.json()

    def get_directions(
        self,
        origin: str,
        destination: str,
        modes: Optional[List[str]] = None,
        departure_now: bool = True,
    ) -> Dict[str, Any]:
        """
        Fetch directions for one or more travel modes.

        Returns a dict keyed by mode with the parsed route summary, or an
        error key if the mode request failed.  Uses the Directions API v1
        (REST), which is globally available and requires only a standard
        Maps API key with Directions enabled.

        Args:
            origin:      Free-text origin (name, address, or lat,lng string).
            destination: Free-text destination.
            modes:       List from {"driving","transit","walking","bicycling"}.
                         Defaults to ["driving","transit"] for Singapore trips.
            departure_now: Pass departure_time=now for transit/driving.
        """
        if not self.is_configured():
            # Return structured api_denied errors for every requested mode so
            # callers receive a consistent dict rather than a raised exception.
            missing_results: Dict[str, Any] = {}
            for m in (modes or ["driving", "transit"]):
                missing_results[m] = {
                    "error": "GOOGLE_MAPS_API_KEY is not set. Add it to your .env file.",
                    "error_type": "api_key_missing",
                    "api_status": "REQUEST_DENIED",
                    "mode": m,
                }
            return missing_results

        modes = modes or ["driving", "transit"]
        results: Dict[str, Any] = {}

        for mode in modes:
            if mode not in _DIRECTIONS_MODES:
                continue
            try:
                params: Dict[str, Any] = {
                    "origin": f"{origin}, Singapore",
                    "destination": f"{destination}, Singapore",
                    "mode": mode,
                    "region": "sg",
                    "language": "en",
                    "key": self.api_key,
                }
                if departure_now and mode in {"driving", "transit"}:
                    params["departure_time"] = "now"

                print(f"[Maps] Directions {mode}: {origin} → {destination}")
                resp = self.session.get(
                    GOOGLE_DIRECTIONS_BASE_URL,
                    params=params,
                    timeout=self.timeout_s,
                )
                resp.raise_for_status()
                data = resp.json()

                status = data.get("status", "UNKNOWN")
                api_message = data.get("error_message", "")
                print(f"[Maps] Directions {mode} status: {status}"
                      + (f" — {api_message}" if api_message else ""))

                if status != "OK":
                    # Classify error so callers can distinguish API-level
                    # problems (key/billing) from query-level problems (no route).
                    if status == "REQUEST_DENIED":
                        error_type = "api_denied"
                        error_detail = (
                            f"Directions API request denied. "
                            f"Check that the Directions API is enabled for your "
                            f"GOOGLE_MAPS_API_KEY and that billing is active. "
                            f"API message: {api_message or 'none'}"
                        )
                    elif status == "ZERO_RESULTS":
                        error_type = "no_route"
                        error_detail = (
                            f"No route found between the given locations for mode={mode}."
                        )
                    elif status == "NOT_FOUND":
                        error_type = "location_not_found"
                        error_detail = f"One or both locations could not be geocoded by Directions API."
                    elif status == "OVER_DAILY_LIMIT" or status == "OVER_QUERY_LIMIT":
                        error_type = "quota_exceeded"
                        error_detail = f"Google Maps API quota exceeded. Try again later."
                    else:
                        error_type = "api_error"
                        error_detail = (
                            f"Directions API returned status={status}. "
                            f"{api_message or ''}"
                        )

                    results[mode] = {
                        "error": error_detail,
                        "error_type": error_type,
                        "api_status": status,
                        "mode": mode,
                    }
                    continue

                route = data["routes"][0]
                leg = route["legs"][0]

                steps_summary = []
                for step in leg.get("steps", []):
                    travel_mode = step.get("travel_mode", mode).lower()
                    instruction = step.get("html_instructions", "")
                    instruction = re.sub(r"<[^>]+>", " ", instruction).strip()
                    duration_s = step.get("duration", {}).get("value", 0)
                    distance_m = step.get("distance", {}).get("value", 0)

                    step_info: Dict[str, Any] = {
                        "mode": travel_mode,
                        "instruction": instruction,
                        "duration_mins": round(duration_s / 60, 1),
                        "distance_m": distance_m,
                    }

                    # Transit-specific detail
                    transit = step.get("transit_details")
                    if transit:
                        dep_stop = (transit.get("departure_stop") or {}).get("name", "")
                        arr_stop = (transit.get("arrival_stop") or {}).get("name", "")
                        line = (transit.get("line") or {})
                        line_name = (
                            line.get("short_name")
                            or line.get("name")
                            or ""
                        )
                        vehicle = ((line.get("vehicle") or {}).get("type") or "").lower()
                        num_stops = transit.get("num_stops", 0)
                        step_info.update({
                            "transit_line": line_name,
                            "transit_vehicle": vehicle,
                            "departure_stop": dep_stop,
                            "arrival_stop": arr_stop,
                            "num_stops": num_stops,
                        })

                    steps_summary.append(step_info)

                # Detect transfer count for transit
                transit_steps = [s for s in steps_summary if s["mode"] == "transit"]
                num_transfers = max(0, len(transit_steps) - 1)

                results[mode] = {
                    "mode": mode,
                    "duration_mins": round(leg["duration"]["value"] / 60, 1),
                    "distance_km": round(leg["distance"]["value"] / 1000, 2),
                    "summary": route.get("summary", ""),
                    "start_address": leg.get("start_address", origin),
                    "end_address": leg.get("end_address", destination),
                    "num_transfers": num_transfers,
                    "steps": steps_summary,
                    "warnings": route.get("warnings", []),
                }

            except Exception as exc:
                print(f"[Maps] Directions {mode} error: {exc}")
                results[mode] = {"error": str(exc), "mode": mode}

        return results


google_maps_client = GoogleMapsClient(settings.GOOGLE_MAPS_API_KEY)