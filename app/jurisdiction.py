"""NZ Building Consents jurisdiction for the Astraea framework."""

from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

from core.jurisdiction import CorpusConfig, JurisdictionBase, SmokeFixture
from core.routing import StatuteRoute

_ROUTES: list[StatuteRoute] = [
    StatuteRoute(
        intent="carport-exemption",
        include_any=("carport", "car port", "covered parking", "garage"),
        forced_sections=(
            "NZLEG/EBWO2020/s11",
            "NZLEG/EBWO2020/s18A",
            "NZLEG/BA2004/s41",
        ),
        synthetic_query="carport exempt building work schedule 1 area height",
    ),
    StatuteRoute(
        intent="detached-building-sleepout",
        include_any=("sleepout", "sleep out", "detached building", "outbuilding", "granny flat", "minor dwelling", "kitset", "prefab"),
        forced_sections=(
            "NZLEG/EBWO2020/s3A",
            "NZLEG/EBWO2020/s3B",
            "NZLEG/EBWO2020/s43",
            "NZLEG/BA2004/s41",
        ),
        synthetic_query="single-storey detached building sleepout exempt 30 square metres lightweight kitset",
    ),
    StatuteRoute(
        intent="shed-barn",
        include_any=("shed", "pole shed", "barn", "hay barn", "farm building", "rural"),
        forced_sections=(
            "NZLEG/EBWO2020/s4A",
            "NZLEG/EBWO2020/s49",
            "NZLEG/BA2004/s41",
        ),
        synthetic_query="pole shed hay barn rural zone exempt building work",
    ),
    StatuteRoute(
        intent="deck-porch-veranda",
        include_any=("deck", "porch", "veranda", "verandah", "pergola"),
        forced_sections=(
            "NZLEG/EBWO2020/s9",
            "NZLEG/EBWO2020/s17A",
            "NZLEG/BA2004/s41",
        ),
        synthetic_query="deck porch veranda exempt building work area height above ground",
    ),
    StatuteRoute(
        intent="awning",
        include_any=("awning", "shade sail", "canopy"),
        forced_sections=(
            "NZLEG/EBWO2020/s7",
            "NZLEG/EBWO2020/s8",
            "NZLEG/EBWO2020/s16A",
            "NZLEG/BA2004/s41",
        ),
        synthetic_query="awning canopy exempt building work size area",
    ),
    StatuteRoute(
        intent="schedule-1-exempt-overview",
        include_any=("schedule 1", "exempt work", "exempt building", "exemption"),
        forced_sections=(
            "NZLEG/BA2004/s41",
        ),
        synthetic_query="schedule 1 exempt building work building act 2004",
    ),
]

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
            qdrant_collection="nz_building_leg",
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
        return _ROUTES

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
            SmokeFixture(
                question="Do I need a building consent for a carport that is 30m2?",
                expected_sections=["NZLEG/EBWO2020/s11", "NZLEG/BA2004/s41"],
                description="carport exemption - EBWO2020 route injection",
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

    @property
    def rewrite_prompt(self) -> str:
        return (
            "Rewrite the following as a concise formal question optimised for retrieving relevant "
            "New Zealand building legislation. Focus on the building work type, size, location, and "
            "the specific legal question (consent required, exempt work, Schedule 1, district plan rules). "
            "Do not mention tenants, landlords, or tribunal decisions. "
            "If a zone context prefix is present (e.g. [Zone context: ...]), strip it - do not include it in the rewrite. "
            "Output only the rewritten question, no explanation, no preamble."
        )

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
