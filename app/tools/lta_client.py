import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Any, Dict, List, Optional
from app.config import settings

LTA_BASE_URL = "https://datamall2.mytransport.sg/ltaodataservice"


class LTADatamallClient:
    def __init__(self, account_key: str, base_url: str = LTA_BASE_URL, timeout_s: int = 20):
        self.account_key = account_key
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s

        self.session = requests.Session()
        retry = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def _headers(self) -> Dict[str, str]:
        return {
            "AccountKey": self.account_key,
            "accept": "application/json",
        }

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        try:
            print(f"[LTA] Calling URL: {url}")
            print(f"[LTA] Params: {params or {}}")

            response = self.session.get(
                url,
                headers=self._headers(),
                params=params or {},
                timeout=self.timeout_s,
            )

            print(f"[LTA] Status Code: {response.status_code}")
            print(f"[LTA] Response Preview: {response.text[:300]}")

            response.raise_for_status()

            if not response.text.strip():
                return {}

            return response.json()

        except requests.exceptions.RequestException as e:
            print(f"[LTA] Request failed for endpoint '{endpoint}': {e}")
            return {
                "error": str(e),
                "endpoint": endpoint,
                "params": params or {},
            }

    def get_paged(self, endpoint: str, page_size: int = 500) -> List[Dict[str, Any]]:
        all_rows: List[Dict[str, Any]] = []
        skip = 0

        while True:
            params = {"$skip": skip}
            payload = self.get(endpoint, params=params)

            if "error" in payload:
                print(f"[LTA] Pagination stopped due to error: {payload['error']}")
                break

            rows = payload.get("value", [])
            if not rows:
                break

            all_rows.extend(rows)

            if len(rows) < page_size:
                break

            skip += page_size

        return all_rows


lta_client = LTADatamallClient(settings.LTA_ACCOUNT_KEY) if settings.LTA_ACCOUNT_KEY else None