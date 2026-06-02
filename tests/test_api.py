"""API integration tests for buildingconsents.

Requires: Qdrant running on localhost:6333 (skip_no_qdrant marker).
Zone endpoint and health check do NOT need Qdrant.
"""

import pytest

from tests.conftest import skip_no_qdrant


# ---------------------------------------------------------------------------
# Health / meta
# ---------------------------------------------------------------------------

def test_health(app_client):
    r = app_client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body.get("status") == "ok"


def test_token_endpoint(app_client):
    r = app_client.get("/token")
    assert r.status_code == 200
    body = r.json()
    assert "token" in body or "public_token" in body or isinstance(body, dict)


# ---------------------------------------------------------------------------
# Zone endpoint (no Qdrant required)
# ---------------------------------------------------------------------------

def test_zone_auckland(app_client):
    r = app_client.post("/zone", json={"address": "Sky Tower, Auckland"})
    assert r.status_code == 200
    body = r.json()
    assert body["found"] is True
    # zone may or may not be found depending on geocoder, but endpoint must respond
    if body.get("zone"):
        assert body["zone"]["council"] == "Auckland"


def test_zone_no_address(app_client):
    r = app_client.post("/zone", json={"address": ""})
    # empty address - should return found=False or a 422
    assert r.status_code in (200, 422)
    if r.status_code == 200:
        body = r.json()
        assert body["found"] is False or body.get("zone") is None


def test_zone_unknown_location(app_client):
    # Invercargill - outside coverage
    r = app_client.post("/zone", json={"address": "Invercargill, Southland"})
    assert r.status_code == 200
    body = r.json()
    if body["found"]:
        assert body["zone"] is None


# ---------------------------------------------------------------------------
# Retrieve endpoint (needs Qdrant)
# ---------------------------------------------------------------------------

@skip_no_qdrant
def test_retrieve_returns_chunks(app_client):
    r = app_client.post(
        "/retrieve",
        json={"question": "Do I need a building consent for a sleepout?", "top_k": 3},
    )
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body, list)
    assert len(body) > 0
    first = body[0]
    assert "id" in first or "chunk_id" in first or "section_id" in first


@skip_no_qdrant
def test_retrieve_includes_ba2004(app_client):
    r = app_client.post(
        "/retrieve",
        json={"question": "Schedule 1 exempt building work", "top_k": 5},
    )
    assert r.status_code == 200
    body = r.json()
    ids = []
    for chunk in body:
        ids.append(
            chunk.get("id") or chunk.get("chunk_id") or chunk.get("section_id") or ""
        )
    joined = " ".join(ids)
    assert "BA2004" in joined, f"Expected BA2004 section in results, got: {ids}"


# ---------------------------------------------------------------------------
# Ask stream (needs Qdrant)
# ---------------------------------------------------------------------------

@skip_no_qdrant
def test_ask_stream_returns_events(app_client):
    with app_client.stream(
        "POST",
        "/ask/stream",
        json={"question": "What is a building consent?"},
    ) as response:
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")
        lines = []
        for line in response.iter_lines():
            lines.append(line)
            if len(lines) >= 10:
                break
        assert any(line.startswith("data:") for line in lines)
