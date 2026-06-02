"""Auckland Unitary Plan zone lookup using geopandas."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import geopandas as gpd
from shapely.geometry import Point

_ZONES_PATH = Path(__file__).parent.parent / "data" / "zones" / "aup_zones.geojson"


@lru_cache(maxsize=1)
def _load_zones() -> gpd.GeoDataFrame:
    return gpd.read_file(_ZONES_PATH).to_crs(epsg=4326)


def lookup_zone(lat: float, lng: float) -> dict | None:
    """Return zone info for a coordinate pair, or None if outside coverage."""
    zones = _load_zones()
    pt = Point(lng, lat)
    match = zones[zones.geometry.contains(pt)]
    if match.empty:
        return None
    row = match.iloc[0]
    return {
        "zone_code": row.get("ZONE_CODE", ""),
        "zone_name": row.get("ZONE_NAME", ""),
        "council": "Auckland",
    }
