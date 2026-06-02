"""Zone lookup across NZ councils using geopandas."""

from __future__ import annotations

from functools import lru_cache

import geopandas as gpd
from shapely.geometry import Point

from app.councils import Council, councils_for_point


@lru_cache(maxsize=16)
def _load(zones_file: str) -> gpd.GeoDataFrame:
    return gpd.read_file(zones_file).to_crs(epsg=4326)


def lookup_zone(lat: float, lng: float) -> dict | None:
    """Return zone info for a coordinate pair, or None if outside all council coverage."""
    candidates = councils_for_point(lat, lng)
    if not candidates:
        return None

    pt = Point(lng, lat)
    for council in candidates:
        if not council.zones_file.exists():
            continue
        gdf = _load(str(council.zones_file))
        match = gdf[gdf.geometry.contains(pt)]
        if not match.empty:
            row = match.iloc[0]
            return {
                "zone_code": int(row.get("ZONE_CODE", 0)),
                "zone_name": str(row.get("ZONE_NAME", "")),
                "council": council.display_name,
            }

    return None
