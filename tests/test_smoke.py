"""Smoke tests: verify legislation retrieval for known building consent questions.

Each test asserts that key legislation sections appear in the top-k results so
we catch retrieval regressions without running the full LLM.
"""

import pytest

from tests.conftest import skip_no_qdrant


def _retrieve(app_client, question: str, top_k: int = 15) -> set:
    r = app_client.post("/retrieve", json={"question": question, "top_k": top_k})
    assert r.status_code == 200
    body = r.json()
    ids: set[str] = set()
    for src in body.get("sources", []):
        if cid := src.get("case_id"):
            ids.add(cid)
    for leg in body.get("legislation", []):
        if cid := leg.get("case_id"):
            ids.add(cid)
    return ids


# ---------------------------------------------------------------------------
# Smoke fixture loop
# ---------------------------------------------------------------------------

@skip_no_qdrant
def test_smoke_fixtures_pass(app_client, jurisdiction):
    failures = []
    for fixture in jurisdiction.smoke_fixtures:
        ids = _retrieve(app_client, fixture.question)
        missing = [s for s in fixture.expected_sections if s not in ids]
        if missing:
            failures.append(
                f"[{fixture.description}]\n"
                f"  question: {fixture.question!r}\n"
                f"  missing:  {missing}\n"
                f"  got:      {sorted(ids)}"
            )
    assert not failures, "Smoke fixture(s) failed:\n\n" + "\n\n".join(failures)


# ---------------------------------------------------------------------------
# BA2004 Schedule 1 core
# ---------------------------------------------------------------------------

@skip_no_qdrant
def test_smoke_sleepout(app_client):
    ids = _retrieve(app_client, "I want to build a 15m2 sleepout in my backyard. Do I need a building consent?")
    assert "NZLEG/BA2004/s41" in ids
    assert "NZLEG/EBWO2020/s43" in ids


@skip_no_qdrant
def test_smoke_schedule1_overview(app_client):
    ids = _retrieve(app_client, "What is exempt building work under Schedule 1 of the Building Act?")
    assert "NZLEG/BA2004/s41" in ids


@skip_no_qdrant
def test_smoke_deck_exemption(app_client):
    ids = _retrieve(app_client, "Do I need a building consent to build a deck that is 100m2 and 800mm above ground?")
    assert "NZLEG/BA2004/s41" in ids


# ---------------------------------------------------------------------------
# EBWO2020 route injection
# ---------------------------------------------------------------------------

@skip_no_qdrant
def test_smoke_carport(app_client):
    ids = _retrieve(app_client, "Do I need a building consent for a carport that is 30m2?")
    assert "NZLEG/EBWO2020/s11" in ids or "NZLEG/EBWO2020/s18A" in ids
    assert "NZLEG/BA2004/s41" in ids


@skip_no_qdrant
def test_smoke_detached_building(app_client):
    ids = _retrieve(app_client, "I want to put up a kitset sleep-out under 30 square metres. Is consent needed?")
    assert any(s in ids for s in ("NZLEG/EBWO2020/s3A", "NZLEG/EBWO2020/s3B", "NZLEG/EBWO2020/s43"))


@skip_no_qdrant
def test_smoke_shed_rural(app_client):
    ids = _retrieve(app_client, "Do I need a building consent for a pole shed on my rural property?")
    assert "NZLEG/EBWO2020/s4A" in ids or "NZLEG/EBWO2020/s49" in ids


@skip_no_qdrant
def test_smoke_veranda(app_client):
    ids = _retrieve(app_client, "Do I need consent for a veranda that is 25 square metres?")
    assert "NZLEG/EBWO2020/s9" in ids or "NZLEG/EBWO2020/s17A" in ids


@skip_no_qdrant
def test_smoke_awning(app_client):
    ids = _retrieve(app_client, "Do I need a building consent for an awning over my shop front?")
    assert any(s in ids for s in ("NZLEG/EBWO2020/s7", "NZLEG/EBWO2020/s8", "NZLEG/EBWO2020/s16A"))


# ---------------------------------------------------------------------------
# Swimming pool
# ---------------------------------------------------------------------------

@skip_no_qdrant
def test_smoke_swimming_pool(app_client):
    ids = _retrieve(app_client, "Do I need a building consent for a swimming pool?")
    assert "NZLEG/BA2004/s162C" in ids or "NZLEG/BA2004/s23" in ids


@skip_no_qdrant
def test_smoke_pool_fencing(app_client):
    ids = _retrieve(app_client, "What are the pool fencing requirements for a residential swimming pool?")
    assert "NZLEG/BA2004/s162C" in ids


# ---------------------------------------------------------------------------
# Solar panels
# ---------------------------------------------------------------------------

@skip_no_qdrant
def test_smoke_solar_panels(app_client):
    ids = _retrieve(app_client, "Do I need consent to install solar panels on my roof?")
    assert any(s in ids for s in (
        "NZLEG/BA2004/s28C", "NZLEG/EBWO2020/s48", "NZLEG/BA2004/s48", "NZLEG/BA2004/s48A"
    ))


# ---------------------------------------------------------------------------
# Water heater
# ---------------------------------------------------------------------------

@skip_no_qdrant
def test_smoke_water_heater(app_client):
    ids = _retrieve(app_client, "Do I need a building consent to replace my hot water cylinder?")
    assert "NZLEG/BA2004/s36" in ids or "NZLEG/BA2004/s38" in ids


# ---------------------------------------------------------------------------
# Outdoor fireplace
# ---------------------------------------------------------------------------

@skip_no_qdrant
def test_smoke_outdoor_fireplace(app_client):
    ids = _retrieve(app_client, "Do I need consent to build a permanent outdoor pizza oven?")
    assert "NZLEG/EBWO2020/s28A" in ids or "NZLEG/BA2004/s28A" in ids


# ---------------------------------------------------------------------------
# Certificate of acceptance
# ---------------------------------------------------------------------------

@skip_no_qdrant
def test_smoke_certificate_of_acceptance(app_client):
    ids = _retrieve(app_client, "I built a deck without consent. How do I get a certificate of acceptance?")
    assert "NZLEG/BA2004/s96" in ids or "NZLEG/BA2004/s97" in ids


# ---------------------------------------------------------------------------
# Ground moisture barrier
# ---------------------------------------------------------------------------

@skip_no_qdrant
def test_smoke_moisture_barrier(app_client):
    ids = _retrieve(app_client, "Do I need consent to install a ground moisture barrier under my house?")
    assert "NZLEG/BA2004/s13A" in ids
