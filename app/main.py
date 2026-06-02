"""Entry point for the NZ Building Consents app."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi import Request

from core.api import create_app

from app.jurisdiction import NZBuildingJurisdiction
from app.zones import prewarm_zones

_QUESTION_LOG = Path("data/question_log.jsonl")

app = create_app(
    NZBuildingJurisdiction(),
    static_dir=Path(__file__).parent / "static",
)

prewarm_zones()


@app.middleware("http")
async def _log_questions(request: Request, call_next):
    if request.method == "POST" and request.url.path == "/ask/stream" and not request.headers.get("X-No-Log"):
        body = await request.body()
        try:
            data = json.loads(body)
            q = data.get("question", "")
            if q:
                _QUESTION_LOG.parent.mkdir(parents=True, exist_ok=True)
                with _QUESTION_LOG.open("a") as _f:
                    _f.write(json.dumps({"ts": datetime.now(timezone.utc).isoformat(), "q": q}) + "\n")
        except Exception:
            pass
        request._body = body
    return await call_next(request)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
