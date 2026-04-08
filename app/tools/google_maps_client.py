import requests
from typing import Any, Dict, Optional

from app.config import settings

GOOGLE_PLACES_BASE_URL = "https://places.googleapis.com/v1"


class GoogleMapsClient:
    def __init__(self, api_key: Optional[str], timeout_s: int = 20):
        self.api_key = api_key
        self.timeout_s = timeout_s
        self.session = requests.Session()

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def _headers(self) -> Dict[str, str]:
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
            headers=self._headers(),
            json=body,
            timeout=self.timeout_s,
        )

        if not response.ok:
            raise RuntimeError(
                f"Google Places error {response.status_code}: {response.text}"
            )

        return response.json()


google_maps_client = GoogleMapsClient(settings.GOOGLE_MAPS_API_KEY)