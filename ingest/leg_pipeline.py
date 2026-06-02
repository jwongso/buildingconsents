"""Ingest NZ building Acts into Qdrant via Astraea's VectorStore and Embedder.

Usage:
    python -m ingest.leg_pipeline                       # all acts
    python -m ingest.leg_pipeline --acts BA2004 RMA1991 # specific acts
    python -m ingest.leg_pipeline --force               # re-ingest existing

Environment:
    QDRANT_URL   (default: http://localhost:6333)
    EMBED_MODEL  (default: same as Astraea core)
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.embedder import Embedder
from core.retriever import VectorStore

from ingest.legislation import ACTS, LegSection, scrape_act

_COLLECTION = "nz_building_leg"
_QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
_CACHE_DIR = Path("data/raw/leg")
_CHUNK_SIZE = 120
_CHUNK_OVERLAP = 20
_UPSERT_BATCH = 200


def _word_count(text: str) -> int:
    return len(text.split())


def _split_words(text: str, size: int, overlap: int) -> list[str]:
    words = text.split()
    chunks, i = [], 0
    while i < len(words):
        chunks.append(" ".join(words[i: i + size]))
        i += size - overlap
    return chunks


def _to_payloads(section: LegSection) -> list[dict]:
    s_ref = f"s{section.section_num}" if section.section_num else ""
    heading = f"{s_ref} {section.section_title}".strip()
    case_id = (
        f"NZLEG/{section.act_code}/s{section.section_num}"
        if section.section_num
        else f"NZLEG/{section.act_code}/{section.dlm_id}"
    )

    full_text = f"{heading}\n\n{section.text}".strip() if heading else section.text

    if _word_count(full_text) <= _CHUNK_SIZE:
        if _word_count(full_text) < 10:
            return []
        return [{
            "chunk_id": f"{case_id}#0",
            "case_id": case_id,
            "court": "NZLEG",
            "court_name": section.act_title,
            "year": section.act_year,
            "title": heading,
            "date": str(section.act_year),
            "url": section.url,
            "text": full_text,
            "chunk_index": 0,
        }]

    payloads = []
    for i, chunk_text in enumerate(_split_words(section.text, _CHUNK_SIZE, _CHUNK_OVERLAP)):
        text = f"{heading}\n\n{chunk_text}".strip() if heading else chunk_text
        payloads.append({
            "chunk_id": f"{case_id}#{i}",
            "case_id": case_id,
            "court": "NZLEG",
            "court_name": section.act_title,
            "year": section.act_year,
            "title": heading,
            "date": str(section.act_year),
            "url": section.url,
            "text": text,
            "chunk_index": i,
        })
    return payloads


async def ingest_act(act_code: str, store: VectorStore, embedder: Embedder, force: bool) -> int:
    sections = await scrape_act(act_code, _CACHE_DIR)
    if not sections:
        return 0

    all_payloads: list[dict] = []
    for s in sections:
        all_payloads.extend(_to_payloads(s))

    if not force:
        existing = store.case_ids_exist([p["case_id"] for p in all_payloads])
        all_payloads = [p for p in all_payloads if p["case_id"] not in existing]

    if not all_payloads:
        print(f"  [{act_code}] all sections already indexed, skipping")
        return 0

    upserted = 0
    for i in range(0, len(all_payloads), _UPSERT_BATCH):
        batch = all_payloads[i: i + _UPSERT_BATCH]
        vectors = await embedder.embed_batch([p["text"] for p in batch])
        store.upsert(vectors=vectors, payloads=batch)
        upserted += len(batch)
        print(f"  [{act_code}] upserted {upserted}/{len(all_payloads)} chunks")
    return upserted


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--acts", nargs="+", default=list(ACTS), choices=list(ACTS))
    parser.add_argument("--force", action="store_true", help="Re-ingest even if already indexed")
    args = parser.parse_args()

    embedder = Embedder()
    store = VectorStore(collection=_COLLECTION, qdrant_url=_QDRANT_URL)
    store.ensure_collection(dim=embedder.dim)

    total = 0
    for act_code in args.acts:
        print(f"\nIngesting {ACTS[act_code]['title']}...")
        total += await ingest_act(act_code, store, embedder, args.force)

    await embedder.close()
    print(f"\nDone. {total} chunks upserted to {_COLLECTION}.")


if __name__ == "__main__":
    asyncio.run(main())
