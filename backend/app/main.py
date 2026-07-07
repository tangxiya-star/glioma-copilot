"""Glioma Copilot API — FastAPI backend.

Scaffold endpoints prove the full path works end-to-end:
  GET  /health        -> app + DB + model status
  POST /api/extract   -> one grounded Claude call (Day 1/2 fleshes this out)

Claude is not the source of truth; it only reasons over retrieved records.
"""

from anthropic import Anthropic
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .config import ANTHROPIC_API_KEY, CLAUDE_MODEL, CORS_ORIGINS
from .db import db_ping

app = FastAPI(title="Glioma Copilot API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = Anthropic(api_key=ANTHROPIC_API_KEY)


@app.get("/")
def root():
    return {"service": "glioma-copilot", "docs": "/docs"}


@app.get("/health")
def health():
    try:
        db_ok = db_ping()
    except Exception:
        db_ok = False
    return {"status": "ok", "db": db_ok, "model": CLAUDE_MODEL}


class ExtractRequest(BaseModel):
    report: str


@app.post("/api/extract")
def extract(req: ExtractRequest):
    """Minimal grounded extraction call — scaffold proof, deepened on Day 1/2."""
    msg = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=500,
        system=(
            "You extract structured molecular markers from a glioma pathology "
            "report. Report only what the text states; if a marker is absent, "
            "omit it. Return concise JSON with a `markers` object."
        ),
        messages=[{"role": "user", "content": req.report}],
    )
    return {"model": CLAUDE_MODEL, "raw": msg.content[0].text}
