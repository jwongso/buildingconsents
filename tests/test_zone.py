"""Zone lookup unit tests - no network or Qdrant required.

All coordinates come from the GeoJSON files already on disk.
"""

import pytest
from app.zones import lookup_zone


def test_auckland_known_address():
    # Ponsonby Road, Auckland - Business Town Centre Zone
    zone = lookup_zone(-36.8573, 174.7479)
    assert zone is not None
    assert zone["council"] == "Auckland"
    assert "Zone" in zone["zone_name"] or zone["zone_name"]


def test_wellington_city_centre():
    # Lambton Quay, Wellington
    zone = lookup_zone(-41.2784, 174.7767)
    assert zone is not None
    assert zone["council"] == "Wellington"
    assert zone["zone_code"]


def test_christchurch_residential():
    # Riccarton Road, Christchurch
    zone = lookup_zone(-43.5318, 172.5847)
    assert zone is not None
    assert zone["council"] == "Christchurch"
    assert zone["zone_name"]


def test_hamilton_city():
    # Garden Place, Hamilton
    zone = lookup_zone(-37.7870, 175.2793)
    assert zone is not None
    assert zone["council"] == "Hamilton"


def test_tauranga_city_centre():
    # Cameron Road, Tauranga
    zone = lookup_zone(-37.6829, 176.1664)
    assert zone is not None
    assert zone["council"] == "Tauranga"
    assert "Business" in zone["zone_name"] or zone["zone_name"]


def test_dunedin_commercial():
    # The Octagon area, Dunedin
    zone = lookup_zone(-45.8742, 170.5036)
    assert zone is not None
    assert zone["council"] == "Dunedin"


def test_outside_coverage_returns_none():
    # Invercargill - not in any covered council
    zone = lookup_zone(-46.4132, 168.3538)
    assert zone is None


def test_zone_code_is_string():
    # Regression: zone_code must not be int (was cast to int in early version)
    zone = lookup_zone(-36.8573, 174.7479)
    assert zone is not None
    assert isinstance(zone["zone_code"], str)
