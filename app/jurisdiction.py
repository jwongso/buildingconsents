"""NZ Building Consents jurisdiction for the Astraea framework."""

from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

from core.jurisdiction import CorpusConfig, JurisdictionBase, SmokeFixture
from core.routing import StatuteRoute

_ROUTES: list[StatuteRoute] = [
    # ---- Structures ----
    StatuteRoute(
        intent="carport-exemption",
        include_any=("carport", "car port", "covered parking"),
        forced_sections=(
            "NZLEG/EBWO2020/s11",
            "NZLEG/EBWO2020/s18A",
            "NZLEG/BA2004/s41",
        ),
        synthetic_query="carport exempt building work area height",
    ),
    StatuteRoute(
        intent="garage",
        include_any=("garage", "workshop", "fully enclosed vehicle"),
        forced_sections=(
            "NZLEG/BA2004/s41",
            "NZLEG/EBWO2020/s3A",
            "NZLEG/EBWO2020/s3B",
        ),
        synthetic_query="garage enclosed building consent exempt detached",
    ),
    StatuteRoute(
        intent="shed-barn",
        include_any=("shed", "pole shed", "barn", "hay barn", "farm building", "man cave", "chicken coop", "summer house", "cabin"),
        forced_sections=(
            "NZLEG/EBWO2020/s4A",
            "NZLEG/EBWO2020/s49",
            "NZLEG/BA2004/s41",
        ),
        synthetic_query="pole shed hay barn rural zone exempt building work",
    ),
    StatuteRoute(
        intent="detached-building-sleepout",
        include_any=("sleepout", "sleep out", "outbuilding", "kitset", "prefab"),
        forced_sections=(
            "NZLEG/EBWO2020/s3A",
            "NZLEG/EBWO2020/s3B",
            "NZLEG/EBWO2020/s43",
            "NZLEG/BA2004/s41",
        ),
        synthetic_query="single-storey detached building sleepout exempt 30 square metres lightweight kitset",
    ),
    StatuteRoute(
        intent="granny-flat-standalone",
        include_any=("granny flat", "minor dwelling", "secondary dwelling", "standalone dwelling", "small standalone"),
        forced_sections=(
            "NZLEG/BA2004/s41",
            "NZLEG/EBWO2020/s3A",
            "NZLEG/EBWO2020/s3B",
        ),
        synthetic_query="granny flat standalone dwelling 70 square metres exempt consent single storey",
    ),
    StatuteRoute(
        intent="deck-porch-veranda",
        include_any=("deck", "sun deck", "porch", "veranda", "verandah", "pergola", "arbour", "platform", "elevated"),
        forced_sections=(
            "NZLEG/EBWO2020/s9",
            "NZLEG/EBWO2020/s17A",
            "NZLEG/BA2004/s41",
        ),
        synthetic_query="deck platform porch veranda elevated structure building consent exempt Schedule 1 height above ground area square metres threshold",
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
        intent="enclosed-veranda-conservatory",
        include_any=("closing in", "enclosed veranda", "enclosed patio", "conservatory", "sun room", "sunroom"),
        forced_sections=(
            "NZLEG/BA2004/s41",
            "NZLEG/EBWO2020/s9",
        ),
        synthetic_query="closing in veranda patio conservatory enclosure building consent",
    ),

    # ---- Swimming pools ----
    StatuteRoute(
        intent="swimming-pool",
        include_any=("swimming pool", "pool", "spa pool", "spa", "hot tub", "paddling pool"),
        forced_sections=(
            "NZLEG/BA2004/s23",
            "NZLEG/BA2004/s162C",
            "NZLEG/BA2004/s162D",
            "NZLEG/BA2004/s21A",
            "NZLEG/BA2004/s41",
        ),
        synthetic_query="swimming pool building consent fencing access restriction residential pool",
    ),

    # ---- Energy and heating ----
    StatuteRoute(
        intent="solar-panels",
        include_any=("solar panel", "solar cell", "photovoltaic", "pv panel", "solar array", "rooftop solar", "ground-mounted solar"),
        forced_sections=(
            "NZLEG/BA2004/s28C",
            "NZLEG/EBWO2020/s48",
            "NZLEG/BA2004/s48",
            "NZLEG/BA2004/s48A",
            "NZLEG/BA2004/s41",
        ),
        synthetic_query="solar panel array ground-mounted roof-mounted exempt building work consent area",
    ),
    StatuteRoute(
        intent="water-heater",
        include_any=("water heater", "hot water cylinder", "hot water tank", "wetback", "continuous hot water", "instant hot water", "gas water"),
        forced_sections=(
            "NZLEG/BA2004/s36",
            "NZLEG/BA2004/s38",
            "NZLEG/BA2004/s35",
            "NZLEG/BA2004/s41",
        ),
        synthetic_query="water heater replacement repair exempt plumber building consent",
    ),
    StatuteRoute(
        intent="outdoor-fireplace",
        include_any=("outdoor fireplace", "pizza oven", "bbq", "barbeque", "fire pit", "outdoor oven", "permanent fireplace"),
        forced_sections=(
            "NZLEG/EBWO2020/s28A",
            "NZLEG/BA2004/s28A",
            "NZLEG/BA2004/s41",
        ),
        synthetic_query="permanent outdoor fireplace oven barbecue exempt building work",
    ),

    # ---- Plumbing and drainage ----
    StatuteRoute(
        intent="plumbing-drainage",
        include_any=("plumbing", "drain", "drainage", "sanitary", "toilet", "sink", "shower", "waste pipe", "grey water", "gully trap"),
        forced_sections=(
            "NZLEG/BA2004/s35",
            "NZLEG/BA2004/s41",
        ),
        synthetic_query="plumbing drainage sanitary alteration exempt authorised drainlayer building consent",
    ),

    # ---- Ground and subfloor ----
    StatuteRoute(
        intent="ground-moisture-barrier",
        include_any=("ground moisture", "moisture barrier", "polythene", "underfloor", "vapour barrier", "plastic sheet"),
        forced_sections=(
            "NZLEG/BA2004/s13A",
            "NZLEG/BA2004/s41",
        ),
        synthetic_query="ground moisture barrier underfloor polythene exempt building work",
    ),

    # ---- Interior alterations ----
    StatuteRoute(
        intent="interior-alterations",
        include_any=("internal wall", "load-bearing wall", "load bearing", "structural wall", "bracing", "doorway", "interior alteration", "non-residential"),
        forced_sections=(
            "NZLEG/BA2004/s10",
            "NZLEG/BA2004/s41",
        ),
        synthetic_query="interior alteration internal wall load-bearing structural building consent",
    ),

    # ---- Consent process ----
    StatuteRoute(
        intent="certificate-of-acceptance",
        include_any=("certificate of acceptance", "unconsented", "without consent", "retrospective consent", "urgent work", "notice to fix"),
        forced_sections=(
            "NZLEG/BA2004/s96",
            "NZLEG/BA2004/s97",
            "NZLEG/BA2004/s98",
            "NZLEG/BA2004/s99",
        ),
        synthetic_query="certificate of acceptance unconsented building work territorial authority application",
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

Base your answers strictly on the legislation and guidance retrieved and provided in the context.
Cite the relevant sections by name (e.g. "Schedule 1, clause 17 of the Building Act 2004" or
"s18A of the Building (Exempt Building Work) Order 2020"). State thresholds, conditions, and
requirements exactly as the cited legislation says - do not guess or summarise from memory.

You do not give legal advice. You help people understand the rules so they can make informed
decisions or know when to seek professional help. If the provided context does not contain
enough information to answer confidently, say so and refer the user to their local council
or canibuildit.govt.nz.

When a zone context prefix is present in the question (e.g. [Zone context: ...]), use it to
give zone-specific answers about permitted activities, height limits, and setback rules."""

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
