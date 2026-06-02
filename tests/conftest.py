"""Shared test fixtures for buildingconsents."""

import httpx
import pytest


def _qdrant_available() -> bool:
    try:
        return httpx.get("http://localhost:6333/collections", timeout=3).status_code == 200
    except Exception:
        return False


qdrant_available = _qdrant_available()
skip_no_qdrant = pytest.mark.skipif(not qdrant_available, reason="Qdrant not available")


@pytest.fixture(scope="session")
def jurisdiction():
    from app.jurisdiction import NZBuildingJurisdiction
    return NZBuildingJurisdiction()


@pytest.fixture(scope="session")
def app_client(jurisdiction):
    from fastapi.testclient import TestClient
    from core.api import create_app
    with TestClient(create_app(jurisdiction)) as client:
        client.headers.update({"X-No-Log": "1"})
        yield client
