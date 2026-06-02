"""NZ Building Consents jurisdiction for the Astraea framework."""

from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

from core.jurisdiction import CorpusConfig, JurisdictionBase, SmokeFixture
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

    @property
    def smoke_fixtures(self) -> list[SmokeFixture]:
        return [
            SmokeFixture(
                question="I want to build a 15m2 sleepout in my backyard. Do I need a building consent?",
                expected_sections=["NZLEG/BA2004/s41", "NZLEG/BA2004/s43"],
                description="exempt work - single-storey detached building under 30m2",
            ),
            SmokeFixture(
                question="Do I need a building consent to build a deck that is 100m2 and 800mm above ground?",
                expected_sections=["NZLEG/BA2004/s41"],
                description="exempt work - deck height and area threshold",
            ),
            SmokeFixture(
                question="What is exempt building work under Schedule 1 of the Building Act?",
                expected_sections=["NZLEG/BA2004/s41"],
                description="schedule 1 exempt building work overview",
            ),
        ]

    def preprocess_question(self, question: str, **context) -> str:
        address = context.get("address")
        if not address:
            return question
        coords = geocode(address)
        if not coords:
            return question
        lat, lng = coords
        zone = lookup_zone(lat, lng)
        if not zone:
            return question
        zone_ctx = (
            f"[Zone context: '{address}' is in {zone['council']} zone '{zone['zone_name']}']\n\n"
        )
        return zone_ctx + question

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
