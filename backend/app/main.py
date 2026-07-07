"""Glioma Copilot API — FastAPI backend.

  GET  /health        -> app + DB + model status
  GET  /api/patient   -> the synthetic demo patient (report text)
  GET  /api/trials    -> live recruiting glioma trials (ClinicalTrials.gov v2)
  POST /api/extract   -> extract structured molecular markers from a report

Claude is not the source of truth; it only reasons over retrieved records.
"""

import json
import re

from anthropic import Anthropic
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .config import AGENT_MODELS, ANTHROPIC_API_KEY, CORS_ORIGINS, model_for
from .db import db_ping
from .patient import SYNTHETIC_PATIENT
from .trials import fetch_glioma_trials

app = FastAPI(title="Glioma Copilot API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = Anthropic(api_key=ANTHROPIC_API_KEY)


def text_from(msg) -> str:
    """Concatenate all text blocks, skipping thinking/other block types."""
    return "".join(
        block.text for block in msg.content if getattr(block, "type", None) == "text"
    )


def parse_json(raw: str):
    """Parse JSON from a model response, tolerating ```json fences / surrounding prose."""
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    # Strip a fenced code block if present, else grab the first {...} span.
    fenced = re.search(r"```(?:json)?\s*(.+?)```", raw, re.DOTALL)
    candidate = fenced.group(1) if fenced else raw
    brace = re.search(r"\{.*\}", candidate, re.DOTALL)
    if brace:
        try:
            return json.loads(brace.group(0))
        except json.JSONDecodeError:
            return None
    return None


@app.get("/")
def root():
    return {"service": "glioma-copilot", "docs": "/docs"}


@app.get("/health")
def health():
    try:
        db_ok = db_ping()
    except Exception:
        db_ok = False
    return {"status": "ok", "db": db_ok, "models": AGENT_MODELS}


@app.get("/api/patient")
def patient():
    """The synthetic demo patient — safe to hardcode, no real PHI."""
    return SYNTHETIC_PATIENT


@app.get("/api/trials")
def trials(limit: int = 20):
    """Live recruiting glioma trials from ClinicalTrials.gov v2."""
    try:
        return {"trials": fetch_glioma_trials(page_size=limit)}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"ClinicalTrials.gov error: {e}")


class ExtractRequest(BaseModel):
    # Optional — defaults to the synthetic demo patient when omitted.
    report: str | None = None


_EXTRACT_SYSTEM = (
    "You extract structured molecular markers from a glioma pathology report. "
    "Report ONLY what the text states — never infer or add markers not present. "
    "For each marker, quote the exact source span it came from.\n\n"
    "Return STRICT JSON, no prose, in this shape:\n"
    "{\n"
    '  "markers": [\n'
    '    {"name": "IDH", "value": "wild-type", "source": "IDH1/2 sequencing: wild-type"}\n'
    "  ],\n"
    '  "prior_treatments": [{"value": "...", "source": "..."}],\n'
    '  "age": {"value": "...", "source": "..."}\n'
    "}"
)


@app.post("/api/extract")
def extract(req: ExtractRequest):
    """Extract structured markers from a report (defaults to the demo patient)."""
    report = req.report or SYNTHETIC_PATIENT["report"]
    model = model_for("extract")
    msg = client.messages.create(
        model=model,
        max_tokens=1000,
        system=_EXTRACT_SYSTEM,
        messages=[{"role": "user", "content": report}],
    )
    raw = text_from(msg)
    return {"model": model, "parsed": parse_json(raw), "raw": raw}
