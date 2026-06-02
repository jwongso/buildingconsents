"""Entry point for the NZ Building Consents app."""

from pathlib import Path

from core.api import create_app

from app.jurisdiction import NZBuildingJurisdiction

app = create_app(
    NZBuildingJurisdiction(),
    static_dir=Path(__file__).parent / "static",
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
