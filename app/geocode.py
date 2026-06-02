"""Address geocoding via Nominatim (OpenStreetMap) - free, no key required."""

from __future__ import annotations

from functools import lru_cache

import httpx

_NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
_TIMEOUT = 10
_HEADERS = {"User-Agent": "buildingconsents.localrun.ai/0.1 (contact: root.aotearoa@gmail.com)"}


@lru_cache(maxsize=512)
def geocode(address: str) -> tuple[float, float] | None:
    """Return (lat, lng) for a NZ address string, or None if not found."""
    try:
        r = httpx.get(
            _NOMINATIM_URL,
            params={"q": address, "format": "json", "limit": 1, "countrycodes": "nz"},
            headers=_HEADERS,
            timeout=_TIMEOUT,
        )
        r.raise_for_status()
        results = r.json()
        if not results:
            return None
        return float(results[0]["lat"]), float(results[0]["lon"])
    except Exception:
        return None
