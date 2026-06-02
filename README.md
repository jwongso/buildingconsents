# NZ Building Consents Help

Free research tool for NZ building consent requirements. Answers questions about the
Building Act 2004, Schedule 1 exempt building work, and district plan zoning rules.

Live at: **https://buildingconsents.localrun.ai**

Built on [Astraea](https://github.com/jwongso/astraea) - an open-justice RAG framework.

---

## What it does

- Answers building consent questions using retrieval-augmented generation (RAG) over
  the Building Act 2004, Resource Management Act 1991, and related MBIE guidance.
- Accepts an optional property address and prepends the zone context (council, zone
  name, zone code) to the question before retrieval and generation.
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

More cities by request - email admin@localrun.ai.

---

## Project layout

```
app/
  main.py          - FastAPI app factory (Astraea create_app)
  jurisdiction.py  - NZBuildingJurisdiction: system prompt, corpus config, /zone route
  zones.py         - GeoJSON zone loader + point-in-polygon lookup (Shapely/GeoPandas)
  geocode.py       - Address -> (lat, lng) via Nominatim (OSM)
  councils.py      - Council registry: name, GeoJSON path, display label
  static/          - Frontend (HTML/CSS/JS, SSE streaming)
ingest/
  leg_pipeline.py  - Legislation ingestion into Qdrant
  download_zones.py - Paginated ArcGIS REST API downloader for all councils
  download_aup_zones.py - Auckland Unitary Plan zone downloader
data/
  zones/           - GeoJSON files per council (not in git - download separately)
  raw/leg/         - Raw legislation XML (not in git)
tests/
  conftest.py      - Shared fixtures (app_client, jurisdiction, skip_no_qdrant)
  test_zone.py     - Zone lookup unit tests (no network or Qdrant required)
  test_api.py      - API integration tests
  test_smoke.py    - Legislation retrieval smoke tests
```

---

## Setup

### Requirements

- Python 3.11+
- [Qdrant](https://qdrant.tech/) running on `localhost:6333`
- Astraea core installed: `pip install -e /path/to/astraea`

### Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Download zone data

Zone GeoJSON files are large and not committed to git. Download them with:

```bash
# All councils
python ingest/download_zones.py

# Single council
python ingest/download_zones.py wellington
```

Auckland zones use a separate script (larger dataset, different API):

```bash
python ingest/download_aup_zones.py
```

### Ingest legislation

```bash
python ingest/leg_pipeline.py
```

This downloads legislation from legislation.govt.nz, chunks it, embeds with a local
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

Returns `{"status": "ok"}`.

### `GET /token`

Returns the public API token for frontend use.

### `POST /zone`

Geocode an NZ address and return its planning zone.

```json
// Request
{"address": "Sky Tower, Auckland"}

// Response (found and in coverage)
{
  "found": true,
  "address": "Sky Tower, Auckland",
  "lat": -36.8484,
  "lng": 174.7622,
  "zone": {
    "zone_code": "BUSL",
    "zone_name": "Business - Local Centre Zone",
    "council": "Auckland"
  }
}
```

### `POST /retrieve`

Retrieve relevant legislation chunks for a question.

```json
// Request
{"question": "Do I need a building consent for a sleepout?", "top_k": 5}

// Response: list of chunk objects with section IDs and scores
```

### `POST /ask/stream`

Stream an answer as Server-Sent Events (SSE).

```json
// Request
{
  "question": "Do I need a building consent for a sleepout?",
  "address": "123 Queen Street, Auckland"
}
```

Events: `data: <text fragment>` ... `data: [DONE]`

---

## Deployment

The service runs as a systemd user service on a Mac Mini M4 Pro, reverse-proxied
through a Cloudflare Tunnel to https://buildingconsents.localrun.ai.

```bash
# Start
systemctl --user start buildingconsents

# Status / logs
systemctl --user status buildingconsents
journalctl --user -u buildingconsents -f
```

Environment variables required in the service unit:

| Variable | Description |
|----------|-------------|
| `PUBLIC_TOKEN` | Bearer token for frontend and REST API access |
| `ALLOWED_ORIGIN` | CORS origin (e.g. https://buildingconsents.localrun.ai) |

---

## Tests

```bash
# Zone unit tests (no Qdrant needed)
pytest tests/test_zone.py -v

# All tests (Qdrant-dependent tests auto-skip if Qdrant is not running)
pytest -v
```

---

## Disclaimer

Zone data is indicative only. District plan boundaries are sourced from council open
data portals and may not reflect the latest plan changes. Always confirm your zone and
applicable rules directly with your council before starting any project.

This tool does not constitute professional advice. Always consult a licensed building
certifier, chartered professional engineer, or your local council before starting
building work.

---

## Licence

MIT. Legislation sourced from legislation.govt.nz (Crown Copyright, open access).
Zone data sourced from council open data portals under Creative Commons Attribution
licences.
