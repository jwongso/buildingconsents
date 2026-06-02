"""Smoke tests: verify legislation retrieval for known building consent questions.

Each SmokeFixture asserts that key legislation sections appear in the top-k
results so we catch retrieval regressions without running the full LLM.
"""

import pytest

from tests.conftest import skip_no_qdrant


@skip_no_qdrant
def test_smoke_fixtures_pass(app_client, jurisdiction):
    """All smoke fixtures must retrieve their expected legislation sections."""
    failures = []

    for fixture in jurisdiction.smoke_fixtures:
        r = app_client.post(
            "/retrieve",
            json={"question": fixture.question, "top_k": 10},
        )
        assert r.status_code == 200, f"[{fixture.description}] /retrieve returned {r.status_code}"

        chunks = r.json()
        retrieved_ids = set()
        for chunk in chunks:
            cid = chunk.get("id") or chunk.get("chunk_id") or chunk.get("section_id") or ""
            retrieved_ids.add(cid)

        missing = [s for s in fixture.expected_sections if s not in retrieved_ids]
        if missing:
            failures.append(
                f"[{fixture.description}]\n"
                f"  question: {fixture.question!r}\n"
                f"  missing:  {missing}\n"
                f"  got:      {sorted(retrieved_ids)}"
            )

    assert not failures, "Smoke fixture(s) failed:\n\n" + "\n\n".join(failures)


@skip_no_qdrant
def test_smoke_sleepout(app_client):
    """Sleepout question must surface BA2004 s41 and s43."""
    r = app_client.post(
        "/retrieve",
        json={
            "question": "I want to build a 15m2 sleepout in my backyard. Do I need a building consent?",
            "top_k": 10,
        },
    )
    assert r.status_code == 200
    chunks = r.json()
    ids = {
        chunk.get("id") or chunk.get("chunk_id") or chunk.get("section_id") or ""
        for chunk in chunks
    }
    assert "NZLEG/BA2004/s41" in ids, f"s41 not in results: {sorted(ids)}"
    assert "NZLEG/BA2004/s43" in ids, f"s43 not in results: {sorted(ids)}"


@skip_no_qdrant
def test_smoke_schedule1_overview(app_client):
    """Schedule 1 overview question must surface BA2004 s41."""
    r = app_client.post(
        "/retrieve",
        json={
            "question": "What is exempt building work under Schedule 1 of the Building Act?",
            "top_k": 10,
        },
    )
    assert r.status_code == 200
    chunks = r.json()
    ids = {
        chunk.get("id") or chunk.get("chunk_id") or chunk.get("section_id") or ""
        for chunk in chunks
    }
    assert "NZLEG/BA2004/s41" in ids, f"s41 not in results: {sorted(ids)}"


@skip_no_qdrant
def test_smoke_deck_exemption(app_client):
    """Deck exemption question must surface BA2004 s41."""
    r = app_client.post(
        "/retrieve",
        json={
            "question": "Do I need a building consent to build a deck that is 100m2 and 800mm above ground?",
            "top_k": 10,
        },
    )
    assert r.status_code == 200
    chunks = r.json()
    ids = {
        chunk.get("id") or chunk.get("chunk_id") or chunk.get("section_id") or ""
        for chunk in chunks
    }
    assert "NZLEG/BA2004/s41" in ids, f"s41 not in results: {sorted(ids)}"
