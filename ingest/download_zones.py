"""Download district plan zone GeoJSON for NZ councils.

Uses ArcGIS REST API with pagination. Normalizes all field names
to ZONE_CODE and ZONE_NAME so zones.py can read them uniformly.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import httpx

_DATA = Path(__file__).parent.parent / "data" / "zones"

COUNCILS = [
    {
        "name": "wellington",
        "out_file": "wdp_zones.geojson",
        "url": "https://gis.wcc.govt.nz/arcgis/rest/services/2024DistrictPlan/2024DistrictPlan/MapServer/122/query",
        "code_field": "DPZoneCode",
        "name_field": "DPZone",
        "where": "1=1",
    },
    {
        "name": "christchurch",
        "out_file": "cdp_zones.geojson",
        "url": "https://gis.ccc.govt.nz/arcgis/rest/services/Hosted/ZoneAndPrecincts_IHPfix/FeatureServer/1/query",
        "code_field": "code",
        "name_field": "type",
        "where": "1=1",
    },
    {
        "name": "hamilton",
        "out_file": "hdp_zones.geojson",
        "url": "https://services1.arcgis.com/R6s0QqCMQdwKY6yp/arcgis/rest/services/DistrictPlan_Zoning/FeatureServer/0/query",
        "code_field": "Zoning_1",
        "name_field": "Zoning_1",
        "where": "1=1",
    },
    {
        "name": "tauranga",
        "out_file": "tdp_zones.geojson",
        "url": "https://services1.arcgis.com/Dd3dlLsFtGLDtMIU/arcgis/rest/services/PlanningZones_Tauranga/FeatureServer/0/query",
        "code_field": "Zone",
        "name_field": "Descriptio",
        "where": "1=1",
    },
    {
        "name": "dunedin",
        "out_file": "ddp_zones.geojson",
        "url": "https://apps.dunedin.govt.nz/arcgis/rest/services/Public/District_Plan/MapServer/110/query",
        "code_field": "LABEL",
        "name_field": "DP_ZONE",
        "where": "1=1",
    },
    {
        "name": "nelson",
        "out_file": "ncc_zones.geojson",
        "url": "https://www.topofthesouthmaps.co.nz/arcgis/rest/services/TopoftheSouthMaps/MapServer/27/query",
        "code_field": "ZONES",
        "name_field": "ZONES",
        "where": "Council='Nelson City Council'",
    },
    {
        "name": "tasman",
        "out_file": "tdc_zones.geojson",
        "url": "https://www.topofthesouthmaps.co.nz/arcgis/rest/services/TopoftheSouthMaps/MapServer/27/query",
        "code_field": "ZONES",
        "name_field": "ZONES",
        "where": "Council='Tasman District Council'",
    },
    {
        "name": "queenstown",
        "out_file": "qldc_zones.geojson",
        "url": "https://gis.qldc.govt.nz/server/rest/services/DistrictPlan/Operative_District_Plan/MapServer/37/query",
        "code_field": "ZONE",
        "name_field": "Zone_Name",
        "where": "1=1",
    },
]

_PAGE_SIZE = 1000
_TIMEOUT = 60.0
_RETRY = 3


def _get_count(client: httpx.Client, url: str, where: str) -> int:
    r = client.get(url, params={"where": where, "returnCountOnly": "true", "f": "json"})
    r.raise_for_status()
    return r.json().get("count", 0)


def _fetch_page(client: httpx.Client, url: str, where: str, offset: int, code_field: str, name_field: str) -> list[dict]:
    """Fetch one page and return GeoJSON features with normalized properties."""
    params = {
        "where": where,
        "outFields": f"{code_field},{name_field}",
        "outSR": "4326",
        "f": "geojson",
        "resultRecordCount": _PAGE_SIZE,
        "resultOffset": offset,
    }
    for attempt in range(_RETRY):
        try:
            r = client.get(url, params=params, timeout=_TIMEOUT)
            r.raise_for_status()
            data = r.json()
            break
        except Exception as exc:
            if attempt == _RETRY - 1:
                raise
            print(f"    retry {attempt + 1} after error: {exc}")
            time.sleep(2 ** attempt)

    features = data.get("features", [])
    normalized = []
    for feat in features:
        props = feat.get("properties") or {}
        geom = feat.get("geometry")
        if not geom:
            continue
        zone_code = str(props.get(code_field) or "").strip()
        zone_name = str(props.get(name_field) or "").strip()
        if not zone_name:
            zone_name = zone_code
        normalized.append({
            "type": "Feature",
            "geometry": geom,
            "properties": {
                "ZONE_CODE": zone_code,
                "ZONE_NAME": zone_name,
            },
        })
    return normalized


def download_council(council: dict) -> None:
    name = council["name"]
    out_path = _DATA / name / council["out_file"]
    print(f"\n[{name}] downloading...")

    with httpx.Client(timeout=_TIMEOUT, follow_redirects=True) as client:
        total = _get_count(client, council["url"], council["where"])
        print(f"  total features: {total}")
        if total == 0:
            print("  SKIP - zero features")
            return

        all_features: list[dict] = []
        offset = 0
        while offset < total:
            page = _fetch_page(
                client, council["url"], council["where"],
                offset, council["code_field"], council["name_field"],
            )
            all_features.extend(page)
            offset += _PAGE_SIZE
            print(f"  fetched {min(offset, total)}/{total}")
            if len(page) == 0:
                break
            time.sleep(0.3)

    geojson = {
        "type": "FeatureCollection",
        "features": all_features,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(geojson))
    print(f"  saved {len(all_features)} features to {out_path.name}")


def main(targets: list[str]) -> None:
    councils = [c for c in COUNCILS if not targets or c["name"] in targets]
    for council in councils:
        download_council(council)
    print("\ndone.")


if __name__ == "__main__":
    main(sys.argv[1:])
