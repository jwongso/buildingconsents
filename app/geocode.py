"""Address geocoding via LINZ Address API (free, NZ-only, no key required)."""

from __future__ import annotations

import httpx

_LINZ_URL = "https://api.linz.govt.nz/v1/search/address"
_TIMEOUT = 10


def geocode(address: str) -> tuple[float, float] | None:
    """Return (lat, lng) for a NZ address string, or None if not found."""
    try:
        r = httpx.get(
            _LINZ_URL,
            params={"q": address, "limit": 1},
            timeout=_TIMEOUT,
        )
        r.raise_for_status()
        features = r.json().get("features", [])
        if not features:
            return None
        coords = features[0]["geometry"]["coordinates"]  # [lng, lat]
        return coords[1], coords[0]
    except Exception:
        return None
