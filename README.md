# NZ Building Consents Help

Free research tool for NZ building consent requirements. Answers questions about the
Building Act 2004, Schedule 1 exempt building work, and district plan zoning rules.

Live at: **https://buildingconsents.localrun.ai**

Built on [Astraea](https://github.com/jwongso/astraea) - an open-justice RAG framework.

---

## What it does

- Answers building consent questions using retrieval-augmented generation (RAG) over
  the Building Act 2004, Building (Exempt Building Work) Order 2020 (EBWO2020),
  Resource Management Act 1991, and related MBIE guidance.
- Accepts an optional property address and prepends the planning zone (council, zone
  name, zone code) to the question before retrieval and generation.
- Zone context prefix is stripped before the rewriter so it biases LLM generation
  toward zone-specific answers without polluting vector retrieval with RMA sections.
- Exposes a `/zone` endpoint that geocodes an NZ address and returns its planning zone.

## Council zone coverage

| Council | District plan | Features |
|---------|---------------|----------|
| Auckland | Auckland Unitary Plan | ~139,000 |
| Wellington | Wellington District Plan 2024 | ~2,700 |
| Christchurch | Christchurch District Plan (IHP) | ~3,800 |
| Hamilton | Hamilton District Plan | ~2,400 |
| Tauranga | Tauranga District Plan | ~2,700 |
| Dunedin | Dunedin District Plan | ~200 |
| Waipa District (Cambridge, Te Awamutu) | Waipa District Plan | 1,339 |
| Palmerston North | PNCC District Plan | 1,422 |
| Rotorua | Rotorua District Plan | 1,893 |

Zone data uses different field naming conventions per council. `zones.py` resolves
`ZONE_NAME` / `Zone` / `ZONE` / `Description` for zone name and `ZONE_CODE` /
`Reference` / `Code` for zone code in priority order, stripping NaN values.

More cities by request - email admin@localrun.ai.

---

## Project layout

```
app/
  main.py          - FastAPI app factory (Astraea create_app) + question log middleware
  jurisdiction.py  - NZBuildingJurisdiction: corpus config, statute routes, /zone route
  zones.py         - GeoJSON zone loader + R-tree point-in-polygon lookup (GeoPandas)
  geocode.py       - Address -> (lat, lng) via Nominatim (OSM), LRU-cached
  councils.py      - Council registry: name, display label, GeoJSON path, bbox
  static/          - Frontend (HTML/CSS/JS, SSE streaming)
    index.html     - Single-page app, 9-council coverage grid
    app.js         - SSE client, markdown renderer (tables, HR, autolinks)
    style.css      - Amber/yellow theme
ingest/
  leg_pipeline.py        - Legislation ingestion into Qdrant (nz_building_leg)
  download_zones.py      - Paginated ArcGIS REST API downloader
  download_aup_zones.py  - Auckland Unitary Plan zone downloader
data/
  zones/           - GeoJSON files per council (not in git - download separately)
    auckland/      - aup_zones.geojson
    waipa/         - wdp_zones.geojson  (Waikato LASS open data)
    palmerston_north/ - pncc_zones.geojson  (geosite.pncc.govt.nz REST API)
    rotorua/       - rdc_zones.geojson  (gis.rdc.govt.nz layer 355)
    ...
  question_log.jsonl   - Every question with timestamp
  feedback.jsonl       - Thumbs up/down ratings
  feedback_full.jsonl  - Full feedback artifact including context_debug
tests/
  conftest.py      - Shared fixtures (app_client, jurisdiction, skip_no_qdrant)
  test_zone.py     - Zone lookup unit tests (no network or Qdrant required)
  test_api.py      - API integration tests
  test_smoke.py    - Legislation retrieval smoke tests (18 tests)
```

---

## Setup

### Requirements

- Python 3.11+
- [Qdrant](https://qdrant.tech/) running on `localhost:6333`
- Redis running on `localhost:6379`
- Astraea core installed: `pip install -e /path/to/astraea`

### Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Download zone data

Zone GeoJSON files are large and not committed to git. Download with:

```bash
python ingest/download_zones.py          # all standard councils
python ingest/download_aup_zones.py      # Auckland (separate, larger dataset)
```

Waipa, Palmerston North, and Rotorua are downloaded from their own REST APIs -
see `data/zones/*/` for the source URLs and the `Add ... zone coverage` commits
for the exact download commands.

### Ingest legislation

```bash
python ingest/leg_pipeline.py
```

Downloads legislation from legislation.govt.nz, chunks it, embeds with a local
embedding model, and upserts into Qdrant collection `nz_building_leg`.

### Run locally

```bash
PUBLIC_TOKEN=your-token uvicorn app.main:app --reload --port 8003
```

Open http://localhost:8003 in your browser.

---

## REST API

All endpoints require `X-Api-Key: <token>` (or `Authorization: Bearer <token>`).
Get the token from `/token`.

### `GET /health`

```json
{"status": "ok", "jurisdiction": "nz-building", "active": 0, "waiting": 0}
```

### `POST /zone`

Geocode an NZ address and return its planning zone.

```json
// Request
{"address": "31 Scott St Cambridge Waikato"}

// Response
{
  "found": true,
  "lat": -37.9065,
  "lng": 175.4778,
  "zone": {
    "zone_code": "",
    "zone_name": "MEDIUM DENSITY RESIDENTIAL ZONE",
    "council": "Waipa District"
  }
}
```

### `POST /retrieve`

Retrieve legislation chunks for a question without LLM generation.

```json
{"question": "Do I need a building consent for a sleepout?", "top_k": 5}
```

### `POST /ask/stream`

Stream an answer as Server-Sent Events. All requests include `feedback_context: true`
so context_debug is always emitted (no debug key required).

```json
{
  "question": "Do I need a building consent for a sleepout?",
  "address": "123 Queen Street, Auckland",
  "feedback_context": true
}
```

SSE event types: `queue`, `sources`, `confidence`, `context_debug`, `token`, `done`, `error`

---

## Statute routing

Keyword-triggered routes force EBWO2020 and BA2004 sections into the anchor context,
ensuring the LLM always sees the correct exemption text regardless of vector retrieval
quality. The zone context prefix is stripped before the rewriter so zone names do not
bias vector search toward RMA/planning sections.

| Route | Keywords (sample) | Forced anchor sections |
|-------|-------------------|------------------------|
| carport-exemption | carport, car port, covered parking | EBWO2020/s11, s18A, BA2004/s41 |
| garage | garage, workshop, fully enclosed vehicle | EBWO2020/s3A, s3B, BA2004/s41 |
| shed-barn | shed, pole shed, barn, hay barn, farm building | EBWO2020/s4A, s49, BA2004/s41 |
| detached-building-sleepout | sleepout, outbuilding, kitset, prefab | EBWO2020/s3A, s3B, s43, BA2004/s41 |
| granny-flat-standalone | granny flat, minor dwelling, secondary dwelling | EBWO2020/s3A, s3B, BA2004/s41 |
| deck-porch-veranda | deck, porch, veranda, pergola, elevated | EBWO2020/s9, s17A, BA2004/s41 |
| awning | awning, shade sail, canopy | EBWO2020/s7, s8, s16A, BA2004/s41 |
| enclosed-veranda-conservatory | conservatory, sun room, enclosed patio | EBWO2020/s9, BA2004/s41 |
| swimming-pool | swimming pool, pool, spa, hot tub | BA2004/s23, s162C, s162D, s21A, s41 |
| solar-panels | solar panel, photovoltaic, ground-mounted solar | EBWO2020/s48, BA2004/s28C, s41 |
| water-heater | water heater, hot water cylinder, wetback | BA2004/s36, s38, s35, s41 |
| outdoor-fireplace | outdoor fireplace, pizza oven, bbq, fire pit | EBWO2020/s28A, BA2004/s28A, s41 |
| plumbing-drainage | plumbing, drain, sanitary, toilet, shower | BA2004/s35, s41 |
| ground-moisture-barrier | moisture barrier, polythene, underfloor | BA2004/s13A, s41 |
| interior-alterations | internal wall, load-bearing, structural wall | BA2004/s10, s41 |
| certificate-of-acceptance | certificate of acceptance, unconsented work | BA2004/s96-s99 |
| schedule-1-exempt-overview | schedule 1, exempt work, exemption | BA2004/s41 |

---

## Concurrency and queuing

Each app process has an in-process asyncio semaphore (`_MAX_CONCURRENT=1`) with a
5-slot waiting queue per IP. Additionally, when `LLM_GLOBAL_CONCURRENCY=1` is set,
all Astraea app processes sharing a Redis instance serialise LLM *generation* through
a Redis-backed atomic counter (Lua `INCR`-if-below-limit). Vector retrieval and anchor
lookup still run in parallel across apps.

This prevents a second app (e.g. tenancy + building both active) from silently stacking
on a `--parallel 1` LLM server. The waiting user sees a `queue` SSE event with position
and estimated wait instead of a silent 50-second spinner.

To disable and let the LLM handle concurrency (e.g. `--parallel 2`): set
`LLM_GLOBAL_CONCURRENCY=0` or omit the variable.

---

## Deployment

Runs as a systemd user service on a Mac Mini M4 Pro (48 GB), reverse-proxied through
a Cloudflare Tunnel.

```bash
systemctl --user start buildingconsents
systemctl --user status buildingconsents
journalctl --user -u buildingconsents -f
```

### Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PUBLIC_TOKEN` | (required) | Bearer token for API access |
| `ALLOWED_ORIGIN` | `*` | CORS allowed origin |
| `LLM_BASE_URL` | `http://localhost:8080/v1` | LLM server endpoint |
| `LLM_MODEL` | `qwen3` | Model name sent to LLM API |
| `LLM_MAX_TOKENS` | `2500` | Max tokens per generation |
| `LLM_GLOBAL_CONCURRENCY` | `0` | Cross-app LLM slot limit (0 = disabled) |
| `QDRANT_URL` | `http://localhost:6333` | Qdrant endpoint |
| `REDIS_URL` | `redis://127.0.0.1:6379/0` | Redis for sessions and global LLM lock |
| `DEBUG_KEY` | (none) | Unlocks debug SSE events |

---

## Tests

```bash
# Zone unit tests (no Qdrant or network needed)
pytest tests/test_zone.py -v

# All tests (Qdrant-dependent tests skip automatically if Qdrant is not running)
pytest -v
```

Test files:

| File | Tests | Notes |
|------|-------|-------|
| `test_zone.py` | 8 | Zone lookup for all 9 councils, no network required |
| `test_api.py` | 6 | Health, token, zone API, retrieve (dict shape), ask/stream |
| `test_smoke.py` | 16 | Legislation retrieval: BA2004 + EBWO2020 route injection |

---

## Feedback and question logs

Every `/ask/stream` request includes `feedback_context: true`, so the server always
emits a full `context_debug` SSE event (rewritten query, chunk previews with scores,
anchor sections, token budget). This is stored in the feedback artifact without
requiring debug mode.

On thumbs-down, `/feedback/full` is called with the complete artifact.

| File | Content |
|------|---------|
| `data/question_log.jsonl` | Timestamp + question for every ask |
| `data/feedback.jsonl` | Rating, question, confidence per thumbs vote |
| `data/feedback_full.jsonl` | Full artifact: question, answer, sources, context_debug |

`context_debug` fields for retrieval diagnosis:

- `original_query` - question after zone prefix injection
- `rewrite_input` - question with zone prefix stripped (what goes to the rewriter)
- `rewritten_query` - rewriter output used for vector search
- `statute_routing` - matched routes, trigger terms, forced sections
- `anchor.sections` - legislation sections fetched verbatim into context
- `chunks` - retrieved vector chunks with score, document_id, preview, full_text
- `budget` - token counts for anchor, chunks, total

---

## Disclaimer

Zone data is indicative only. District plan boundaries are sourced from council open
data portals and may not reflect the latest plan changes. Always confirm your zone
and applicable rules directly with your council before starting any project.

This tool does not constitute professional advice. Always consult a licensed building
certifier, chartered professional engineer, or your local council before starting
building work.

---

## Licence

MIT. Legislation sourced from legislation.govt.nz (Crown Copyright, open access).
Zone data sourced from council open data portals under Creative Commons Attribution
licences.
