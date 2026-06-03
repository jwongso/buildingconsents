"""Council registry - bounding boxes for fast lookup, zone file paths."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

_DATA = Path(__file__).parent.parent / "data" / "zones"


@dataclass(frozen=True)
class Council:
    name: str
    display_name: str
    zones_file: Path
    # WGS84 bounding box (lat_min, lat_max, lng_min, lng_max) for fast rejection
    bbox: tuple[float, float, float, float]


COUNCILS: list[Council] = [
    Council(
        name="auckland",
        display_name="Auckland",
        zones_file=_DATA / "auckland" / "aup_zones.geojson",
        bbox=(-37.30, -36.20, 174.20, 175.30),
    ),
    Council(
        name="wellington",
        display_name="Wellington",
        zones_file=_DATA / "wellington" / "wdp_zones.geojson",
        bbox=(-41.60, -40.80, 174.60, 175.20),
    ),
    Council(
        name="christchurch",
        display_name="Christchurch",
        zones_file=_DATA / "christchurch" / "cdp_zones.geojson",
        bbox=(-43.70, -43.30, 172.40, 172.90),
    ),
    Council(
        name="hamilton",
        display_name="Hamilton",
        zones_file=_DATA / "hamilton" / "hdp_zones.geojson",
        bbox=(-37.90, -37.60, 175.20, 175.40),
    ),
    Council(
        name="tauranga",
        display_name="Tauranga",
        zones_file=_DATA / "tauranga" / "tdp_zones.geojson",
        bbox=(-37.80, -37.55, 175.90, 176.30),
    ),
    Council(
        name="dunedin",
        display_name="Dunedin",
        zones_file=_DATA / "dunedin" / "ddp_zones.geojson",
        bbox=(-46.10, -45.60, 170.20, 170.80),
    ),
    Council(
        name="waipa",
        display_name="Waipa District",
        zones_file=_DATA / "waipa" / "wdp_zones.geojson",
        bbox=(-38.20, -37.76, 175.05, 175.66),
    ),
    Council(
        name="palmerston_north",
        display_name="Palmerston North",
        zones_file=_DATA / "palmerston_north" / "pncc_zones.geojson",
        bbox=(-40.53, -40.24, 175.49, 175.80),
    ),
    Council(
        name="rotorua",
        display_name="Rotorua",
        zones_file=_DATA / "rotorua" / "rdc_zones.geojson",
        bbox=(-38.57, -37.93, 175.98, 176.62),
    ),
    Council(
        name="nelson",
        display_name="Nelson",
        zones_file=_DATA / "nelson" / "ncc_zones.geojson",
        bbox=(-41.40, -41.15, 173.10, 173.45),
    ),
    Council(
        name="tasman",
        display_name="Tasman District",
        zones_file=_DATA / "tasman" / "tdc_zones.geojson",
        bbox=(-41.80, -40.55, 172.10, 173.65),
    ),
    Council(
        name="queenstown",
        display_name="Queenstown-Lakes",
        zones_file=_DATA / "queenstown" / "qldc_zones.geojson",
        bbox=(-45.10, -44.35, 168.10, 169.35),
    ),
]


def councils_for_point(lat: float, lng: float) -> list[Council]:
    """Return councils whose bounding box contains the point (fast pre-filter)."""
    return [
        c for c in COUNCILS
        if c.bbox[0] <= lat <= c.bbox[1] and c.bbox[2] <= lng <= c.bbox[3]
    ]
