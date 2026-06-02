#!/usr/bin/env python3
"""Download Auckland Unitary Plan zone boundaries from Auckland Council ArcGIS.

Fetches all ~130k zone polygons in paginated batches, resolves numeric zone
codes to human-readable names, and saves as GeoJSON in WGS84.

Usage:
    python ingest/download_aup_zones.py
    python ingest/download_aup_zones.py --out data/zones/auckland/aup_zones.geojson
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import httpx

_SERVICE = (
    "https://services1.arcgis.com/n4yPwebTjJCmXB6W/arcgis/rest"
    "/services/Unitary_Plan_Base_Zone/FeatureServer/0"
)
_BATCH = 2000
_TIMEOUT = 60

# Numeric ZONE code -> human-readable name (from service domain dUPZone)
ZONE_NAMES: dict[int, str] = {
    1: "Business - Business Park Zone",
    3: "Rural - Countryside Living Zone",
    4: "Future Urban Zone",
    5: "Business - Heavy Industry Zone",
    7: "Business - Local Centre Zone",
    8: "Residential - Terrace Housing and Apartment Building Zone",
    10: "Business - Metropolitan Centre Zone",
    11: "Rural - Mixed Rural Zone",
    12: "Business - Mixed Use Zone",
    15: "Rural - Rural Conservation Zone",
    16: "Rural - Rural Production Zone",
    17: "Business - Light Industry Zone",
    18: "Residential - Mixed Housing Suburban Zone",
    19: "Residential - Single House Zone",
    20: "Residential - Rural and Coastal Settlement Zone",
    22: "Business - Town Centre Zone",
    23: "Residential - Large Lot Zone",
    25: "Water",
    26: "Strategic Transport Corridor Zone",
    27: "Road",
    30: "Coastal - General Coastal Marine Zone",
    31: "Open Space - Conservation Zone",
    32: "Open Space - Informal Recreation Zone",
    33: "Open Space - Sport and Active Recreation Zone",
    34: "Open Space - Community Zone",
    35: "Business - City Centre Zone",
    37: "Coastal - Minor Port Zone",
    39: "Coastal - Defence Zone",
    40: "Coastal - Marina Zone",
    41: "Coastal - Mooring Zone",
    43: "Hauraki Gulf Islands",
    44: "Business - Neighbourhood Centre Zone",
    45: "Coastal - Ferry Terminal Zone",
    46: "Rural - Rural Coastal Zone",
    49: "Business - General Business Zone",
    51: "Special Purpose - Quarry Zone",
    52: "Special Purpose - Maori Purpose Zone",
    53: "Special Purpose - Cemetery Zone",
    54: "Special Purpose - Major Recreation Facility Zone",
    55: "Special Purpose - Healthcare Facility and Hospital Zone",
    56: "Special Purpose - Airports and Airfields Zone",
    59: "Coastal - Coastal Transition Zone",
    60: "Residential - Mixed Housing Urban Zone",
    61: "Green Infrastructure Corridor",
    62: "Open Space - Civic Spaces Zone",
    63: "Special Purpose - School Zone",
    64: "Special Purpose - Tertiary Education Zone",
    65: "Ardmore Airport",
    66: "Ardmore Airport Residential",
    67: "Special Purpose - Landfill Zone",
    68: "Rural - Waitakere Foothills Zone",
    69: "Rural - Waitakere Ranges Zone",
    70: "Two-Storey Single Dwelling Residential Area",
    71: "Two-Storey Medium Density Residential Area",
    72: "Residential - Low Density Residential Zone",
}


def _fetch_batch(offset: int) -> list[dict]:
    r = httpx.get(
        f"{_SERVICE}/query",
        params={
            "where": "1=1",
            "outFields": "OBJECTID,ZONE,GROUPZONE",
            "outSR": "4326",
            "f": "geojson",
            "resultOffset": offset,
            "resultRecordCount": _BATCH,
        },
        timeout=_TIMEOUT,
    )
    r.raise_for_status()
    return r.json().get("features", [])


def _enrich(feature: dict) -> dict:
    props = feature.get("properties", {})
    zone_code = int(props.get("ZONE", 0) or 0)
    props["ZONE_CODE"] = zone_code
    props["ZONE_NAME"] = ZONE_NAMES.get(zone_code, f"Zone {zone_code}")
    return feature


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out",
        default="data/zones/auckland/aup_zones.geojson",
        help="Output GeoJSON path",
    )
    args = parser.parse_args()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    features = []
    offset = 0
    while True:
        print(f"  fetching offset {offset}...", file=sys.stderr)
        batch = _fetch_batch(offset)
        if not batch:
            break
        features.extend(_enrich(f) for f in batch)
        if len(batch) < _BATCH:
            break
        offset += _BATCH

    geojson = {
        "type": "FeatureCollection",
        "features": features,
    }
    out.write_text(json.dumps(geojson))
    print(f"Wrote {len(features)} features to {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
