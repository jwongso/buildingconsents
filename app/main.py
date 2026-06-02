"""Entry point for the NZ Building Consents app."""

from astraea.core.app import create_app

from app.jurisdiction import NZBuildingJurisdiction

app = create_app(NZBuildingJurisdiction())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
