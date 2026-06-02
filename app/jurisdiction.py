"""NZ Building Consents jurisdiction for the Astraea framework."""

from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

from core.jurisdiction import CorpusConfig, JurisdictionBase
from core.routing import StatuteRoute

from app.geocode import geocode
from app.zones import lookup_zone


class ZoneRequest(BaseModel):
    address: str


class NZBuildingJurisdiction(JurisdictionBase):

    @property
    def name(self) -> str:
        return "nz-building"

    @property
    def description(self) -> str:
        return "Free NZ building consents and zone lookup - buildingconsents.localrun.ai"

    @property
    def corpus(self) -> CorpusConfig:
        return CorpusConfig(
            qdrant_collection="nz_building",
            courts=[],
            leg_collection="nz_building_leg",
        )

    @property
    def system_prompt(self) -> str:
        return """\
You are a helpful assistant specialising in New Zealand building and resource consent law.
You answer questions about the Building Act 2004, Schedule 1 exemptions (exempt building work),
district plan zoning rules, and related MBIE guidance.

You cite the relevant sections of legislation and planning rules in your answers.
You do not give legal advice - you help people understand the rules so they can
make informed decisions or know when to seek professional help.

When zone information is provided in the question context, use it to give zone-specific answers
about height limits, setback rules, site coverage, and permitted activities.

If you do not have enough information to answer confidently, say so clearly rather than guessing."""

    @property
    def routes(self) -> list[StatuteRoute]:
        return []

    def get_scraper(self):
        raise NotImplementedError("Use ingest/leg_pipeline.py to populate the corpus.")

    def register_routes(self, app: FastAPI) -> None:
        """Add /zone endpoint for address -> zone lookup."""

        @app.post("/zone")
        async def zone_lookup(req: ZoneRequest) -> dict:
            """Geocode an NZ address and return its planning zone."""
            coords = geocode(req.address)
            if not coords:
                return {"found": False, "address": req.address, "zone": None, "error": "Address not found"}
            lat, lng = coords
            zone = lookup_zone(lat, lng)
            if not zone:
                return {
                    "found": True,
                    "address": req.address,
                    "lat": lat,
                    "lng": lng,
                    "zone": None,
                    "error": "Location found but outside covered council boundaries",
                }
            return {
                "found": True,
                "address": req.address,
                "lat": lat,
                "lng": lng,
                "zone": zone,
            }
