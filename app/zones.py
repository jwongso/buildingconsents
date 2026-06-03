"""Zone lookup across NZ councils using geopandas."""

from __future__ import annotations

import threading
from functools import lru_cache

import geopandas as gpd
from shapely.geometry import Point

from app.councils import COUNCILS, Council, councils_for_point


def _field(row, *names: str) -> str:
    """Return the first non-empty, non-NaN value from the given field names."""
    for name in names:
        val = row.get(name)
        if val is not None:
            s = str(val).strip()
            if s and s.lower() != "nan":
                return s
    return ""


@lru_cache(maxsize=16)
def _load(zones_file: str) -> gpd.GeoDataFrame:
    return gpd.read_file(zones_file).to_crs(epsg=4326)


def prewarm_zones() -> None:
    """Load all council zone files into the lru_cache in a background thread."""
    def _load_all():
        for council in COUNCILS:
            if council.zones_file.exists():
                _load(str(council.zones_file))
    threading.Thread(target=_load_all, daemon=True, name="zone-prewarm").start()


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
        # R-tree bbox candidates first (O(log n)), exact check on the tiny subset
        bbox_idx = list(gdf.sindex.query(pt))
        if not bbox_idx:
            # Try small buffer to catch points near polygon edges (road gaps)
            bbox_idx = list(gdf.sindex.query(pt.buffer(0.0003)))
        if not bbox_idx:
            continue
        subset = gdf.iloc[bbox_idx]
        match = subset[subset.geometry.contains(pt)]
        if match.empty:
            # ~30m buffer for road-gap tolerance (point on boundary or road centerline)
            pt_buf = pt.buffer(0.0003)
            match = subset[subset.geometry.intersects(pt_buf)]
        if not match.empty:
            row = match.iloc[0]
            return {
                "zone_code": _field(row, "ZONE_CODE", "Reference", "Code"),
                "zone_name": _field(row, "ZONE_NAME", "Zone", "ZONE", "Description"),
                "council": council.display_name,
            }

    return None
