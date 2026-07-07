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

from .classify import classify_who_cns5
from .config import AGENT_MODELS, ANTHROPIC_API_KEY, CORS_ORIGINS, model_for
from .db import (
    db_counts,
    db_ping,
    init_schema,
    store_eligibility_results,
    upsert_patient,
    upsert_trials,
)
from .patient import SYNTHETIC_PATIENT, SYNTHETIC_PATIENTS, get_patient
from .trials import fetch_glioma_trials, fetch_trial

app = FastAPI(title="Glioma Copilot API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    # Allow any Vercel deployment (prod + preview) without hardcoding the URL.
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = Anthropic(api_key=ANTHROPIC_API_KEY)


@app.on_event("startup")
def _startup():
    """Ensure tables exist. Non-fatal if the DB is briefly unreachable."""
    try:
        init_schema()
    except Exception as e:
        print(f"[startup] schema init skipped: {e}")


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


@app.get("/api/patients")
def patients():
    """List the synthetic demo cases (spanning the glioma spectrum)."""
    return {"patients": [{"id": p["id"], "label": p["label"]} for p in SYNTHETIC_PATIENTS]}


@app.get("/api/patient")
def patient(id: str | None = None):
    """A synthetic demo patient by id (defaults to Case 001). No real PHI."""
    return get_patient(id)


def condition_for_diagnosis(diagnosis: str | None) -> str:
    """Map a WHO CNS5 diagnosis to a ClinicalTrials.gov condition query (candidate scoping)."""
    d = (diagnosis or "").lower()
    if "glioblastoma" in d:
        return "glioblastoma"
    if "oligodendroglioma" in d:
        return "oligodendroglioma"
    if "astrocytoma" in d:
        return "astrocytoma"
    return "glioma"


@app.get("/api/trials")
def trials(limit: int = 20, condition: str = "glioma"):
    """Live recruiting trials for a condition (also cached to DB).

    Pass `condition` (e.g. from the patient's diagnosis) to narrow candidates to
    the patient's tumor type. Defaults to broad 'glioma'.
    """
    try:
        result = fetch_glioma_trials(page_size=limit, condition=condition)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"ClinicalTrials.gov error: {e}")
    try:
        upsert_trials(result)
    except Exception as e:
        print(f"[trials] store skipped: {e}")
    return {"trials": result}


@app.get("/api/db/summary")
def db_summary():
    """Row counts — proves pulled trials + patients are stored and queryable."""
    return db_counts()


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


# --- WHO CNS5 classification: Claude normalizes -> deterministic rule engine ---

_PROFILE_SYSTEM = (
    "You read a glioma pathology/molecular report and normalize it into fixed "
    "fields for a downstream WHO CNS5 rule engine. You do NOT diagnose — you only "
    "report what the text states, each field with the exact source span it came "
    "from. If a field is not stated or is pending/untested, use value \"unknown\".\n\n"
    "Return STRICT JSON only, every field an object {\"value\": <enum>, \"source\": <quote>}:\n"
    "{\n"
    '  "idh": {"value": "mutant|wildtype|unknown", "source": ""},\n'
    '  "codeletion_1p19q": {"value": "codeleted|intact|unknown", "source": ""},\n'
    '  "cdkn2a_b": {"value": "homozygous_deletion|retained|unknown", "source": ""},\n'
    '  "egfr_amp": {"value": "amplified|not_amplified|unknown", "source": ""},\n'
    '  "tert_promoter": {"value": "mutated|wildtype|unknown", "source": ""},\n'
    '  "chr7_10": {"value": "gain7_loss10|no|unknown", "source": ""},\n'
    '  "microvascular_proliferation": {"value": "present|absent|unknown", "source": ""},\n'
    '  "necrosis": {"value": "present|absent|unknown", "source": ""},\n'
    '  "atrx": {"value": "lost|retained|unknown", "source": ""},\n'
    '  "mgmt": {"value": "methylated|unmethylated|unknown", "source": ""},\n'
    '  "h3k27m": {"value": "mutant|not_detected|unknown", "source": ""}\n'
    "}"
)


@app.post("/api/classify")
def classify(req: ExtractRequest):
    """Report -> normalized profile (Claude) -> WHO CNS5 diagnosis (deterministic)."""
    report = req.report or SYNTHETIC_PATIENT["report"]
    model = model_for("classify")
    msg = client.messages.create(
        model=model,
        max_tokens=1200,
        system=_PROFILE_SYSTEM,
        messages=[{"role": "user", "content": report}],
    )
    profile = parse_json(text_from(msg))
    if profile is None:
        raise HTTPException(status_code=502, detail="Could not normalize report into a profile")
    classification = classify_who_cns5(profile)
    # Persist the demo patient with its profile + classification (best-effort).
    if req.report is None:
        try:
            upsert_patient(SYNTHETIC_PATIENT, profile, classification)
        except Exception as e:
            print(f"[classify] store skipped: {e}")
    return {
        "model": model,
        "profile": profile,
        "classification": classification,
        "trial_condition": condition_for_diagnosis(classification.get("diagnosis")),
    }


# --- Day 3: per-criterion Trial Fit Assessment (met / not-met / unknown) ---

_FIT_SYSTEM = (
    "You are a clinical-trial eligibility screener for a neuro-oncology clinician. "
    "Given a PATIENT REPORT and a trial's ELIGIBILITY CRITERIA, split the criteria "
    "into discrete inclusion/exclusion items and judge each against the patient.\n\n"
    "VERDICT = the patient's compatibility with enrollment on that line:\n"
    "  - \"met\": the patient satisfies this line (for an EXCLUSION, means the patient "
    "does NOT have the excluding condition — handle negation carefully, e.g. "
    "'no prior bevacizumab' + patient never received it => met).\n"
    "  - \"not_met\": the patient clearly fails/violates this line.\n"
    "  - \"unknown\": the patient's data does not say; state what test/info is needed.\n\n"
    "Rules: judge ONLY from the report — never assume unstated facts. For every item, "
    "quote the exact eligibility line in `citation`. Focus on the most decision-relevant "
    "criteria (up to ~14). Return STRICT JSON only:\n"
    "{\n"
    '  "items": [\n'
    '    {"criterion": "", "kind": "inclusion|exclusion", "verdict": "met|not_met|unknown", '
    '"citation": "<exact eligibility line>", "rationale": "<short, what in the report decided it>"}\n'
    "  ]\n"
    "}"
)


class FitRequest(BaseModel):
    nct_id: str
    patient_id: str | None = None


@app.post("/api/fit")
def fit(req: FitRequest):
    """Assess one trial's eligibility criteria against one patient, per criterion."""
    patient = get_patient(req.patient_id)
    trial = fetch_trial(req.nct_id)
    if trial is None:
        raise HTTPException(status_code=404, detail=f"Trial {req.nct_id} not found")
    if not trial.get("eligibility"):
        raise HTTPException(status_code=422, detail="Trial has no eligibility text")

    model = model_for("fit")
    user = (
        f"PATIENT REPORT:\n{patient['report']}\n\n"
        f"TRIAL {trial['nct_id']} — {trial['title']}\n"
        f"ELIGIBILITY CRITERIA:\n{trial['eligibility']}"
    )
    msg = client.messages.create(
        model=model,
        max_tokens=8000,
        system=_FIT_SYSTEM,
        messages=[{"role": "user", "content": user}],
    )
    parsed = parse_json(text_from(msg))
    if parsed is None or "items" not in parsed:
        raise HTTPException(status_code=502, detail="Could not parse fit assessment")
    items = parsed["items"]

    summary = {"met": 0, "not_met": 0, "unknown": 0}
    for it in items:
        if it.get("verdict") in summary:
            summary[it["verdict"]] += 1

    try:
        upsert_patient(patient)        # ensure FK targets exist before storing results
        upsert_trials([trial])
        store_eligibility_results(patient["id"], trial["nct_id"], items)
    except Exception as e:
        print(f"[fit] store skipped: {e}")

    return {
        "model": model,
        "patient_id": patient["id"],
        "trial": {"nct_id": trial["nct_id"], "title": trial["title"], "url": trial["url"],
                  "locations": trial["locations"]},
        "items": items,
        "summary": summary,
    }
