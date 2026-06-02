"""Smoke tests: verify legislation retrieval for known building consent questions.

Each test asserts that key legislation sections appear in the top-k results so
we catch retrieval regressions without running the full LLM.
"""

import pytest

from tests.conftest import skip_no_qdrant


def _ids(chunks: list) -> set:
    return {
        chunk.get("id") or chunk.get("chunk_id") or chunk.get("section_id") or ""
        for chunk in chunks
    }


def _retrieve(app_client, question: str, top_k: int = 15) -> set:
    r = app_client.post("/retrieve", json={"question": question, "top_k": top_k})
    assert r.status_code == 200
    return _ids(r.json())


# ---------------------------------------------------------------------------
# Smoke fixture loop
# ---------------------------------------------------------------------------

@skip_no_qdrant
def test_smoke_fixtures_pass(app_client, jurisdiction):
    """All smoke fixtures must retrieve their expected legislation sections."""
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
# BA2004 Schedule 1 - core exempt work
# ---------------------------------------------------------------------------

@skip_no_qdrant
def test_smoke_sleepout(app_client):
    ids = _retrieve(app_client, "I want to build a 15m2 sleepout in my backyard. Do I need a building consent?")
    assert "NZLEG/BA2004/s41" in ids, f"BA2004/s41 missing: {sorted(ids)}"
    assert "NZLEG/BA2004/s43" in ids, f"BA2004/s43 missing: {sorted(ids)}"


@skip_no_qdrant
def test_smoke_schedule1_overview(app_client):
    ids = _retrieve(app_client, "What is exempt building work under Schedule 1 of the Building Act?")
    assert "NZLEG/BA2004/s41" in ids, f"BA2004/s41 missing: {sorted(ids)}"


@skip_no_qdrant
def test_smoke_deck_exemption(app_client):
    ids = _retrieve(app_client, "Do I need a building consent to build a deck that is 100m2 and 800mm above ground?")
    assert "NZLEG/BA2004/s41" in ids, f"BA2004/s41 missing: {sorted(ids)}"


# ---------------------------------------------------------------------------
# EBWO2020 route injection tests
# ---------------------------------------------------------------------------

@skip_no_qdrant
def test_smoke_carport_ebwo(app_client):
    """Carport question must surface EBWO2020 carport sections via route injection."""
    ids = _retrieve(app_client, "Do I need a building consent for a carport? It will be 30m2.")
    assert "NZLEG/EBWO2020/s11" in ids or "NZLEG/EBWO2020/s18A" in ids, (
        f"EBWO2020 carport section missing: {sorted(ids)}"
    )
    assert "NZLEG/BA2004/s41" in ids, f"BA2004/s41 missing: {sorted(ids)}"


@skip_no_qdrant
def test_smoke_detached_building_ebwo(app_client):
    """Detached building (kitset/prefab) must surface EBWO2020 s3A/s3B/s43."""
    ids = _retrieve(app_client, "I want to put up a kitset sleep-out under 30 square metres. Is consent needed?")
    assert any(s in ids for s in ("NZLEG/EBWO2020/s3A", "NZLEG/EBWO2020/s3B", "NZLEG/EBWO2020/s43")), (
        f"EBWO2020 detached building section missing: {sorted(ids)}"
    )


@skip_no_qdrant
def test_smoke_shed_rural(app_client):
    """Shed/barn question must surface EBWO2020 s4A/s49."""
    ids = _retrieve(app_client, "Do I need a building consent for a pole shed on my rural property?")
    assert "NZLEG/EBWO2020/s4A" in ids or "NZLEG/EBWO2020/s49" in ids, (
        f"EBWO2020 shed section missing: {sorted(ids)}"
    )


@skip_no_qdrant
def test_smoke_deck_ebwo(app_client):
    """Deck/veranda question must surface EBWO2020 s9/s17A."""
    ids = _retrieve(app_client, "Do I need consent for a veranda that is 25 square metres?")
    assert "NZLEG/EBWO2020/s9" in ids or "NZLEG/EBWO2020/s17A" in ids, (
        f"EBWO2020 veranda section missing: {sorted(ids)}"
    )


@skip_no_qdrant
def test_smoke_awning(app_client):
    """Awning question must surface EBWO2020 awning sections."""
    ids = _retrieve(app_client, "Do I need a building consent for an awning over my shop front?")
    assert any(s in ids for s in ("NZLEG/EBWO2020/s7", "NZLEG/EBWO2020/s8", "NZLEG/EBWO2020/s16A")), (
        f"EBWO2020 awning section missing: {sorted(ids)}"
    )
