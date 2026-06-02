"""NZ Building Consents jurisdiction for the Astraea framework."""

from __future__ import annotations

from astraea.core.jurisdiction import JurisdictionBase, CorpusConfig

from app.geocode import geocode
from app.zones import lookup_zone


class NZBuildingJurisdiction(JurisdictionBase):
    name = "nz-building"
    display_name = "NZ Building Consents"

    corpus = CorpusConfig(
        qdrant_collection="nz_building",
        leg_collection="nz_building_leg",
    )

    system_prompt = """\
You are a helpful assistant specialising in New Zealand building and resource consent law.
You answer questions about the Building Act 2004, Schedule 1 exemptions, district plan
zoning rules, and related MBIE guidance.

You cite the relevant sections of legislation and planning rules in your answers.
You do not give legal advice - you help people understand the rules so they can
make informed decisions or know when to seek professional help.

When zone information is provided in the question, use it to give zone-specific answers
about height limits, setback rules, site coverage, and permitted activities."""

    def enrich_question(self, question: str, address: str | None = None) -> str:
        """Prepend zone context when an address resolves to a known council zone."""
        if not address:
            return question
        coords = geocode(address)
        if not coords:
            return question
        zone = lookup_zone(*coords)
        if not zone:
            return question
        context = (
            f"[Zone context: {address} is in the {zone['zone_name']} "
            f"({zone['zone_code']}) zone under the {zone['council']} district plan]\n\n"
        )
        return context + question
