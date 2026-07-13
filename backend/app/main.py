"""Glioma Copilot API — FastAPI backend.

  GET  /health        -> app + DB + model status
  GET  /api/patient   -> the synthetic demo patient (report text)
  GET  /api/trials    -> live recruiting glioma trials (ClinicalTrials.gov v2)
  POST /api/extract   -> extract structured molecular markers from a report

Claude is not the source of truth; it only reasons over retrieved records.
"""

import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

from anthropic import Anthropic
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from .classify import classify_who_cns5
from .config import AGENT_MODELS, ANTHROPIC_API_KEY, CORS_ORIGINS, model_for, tuning_for
from .db import (
    db_counts,
    db_ping,
    get_drug_cache,
    get_eligibility_results,
    init_schema,
    put_drug_cache,
    store_eligibility_results,
    upsert_patient,
    upsert_trials,
)
from .drugs import normalize_drug
from .evidence import lookup as evidence_lookup
from .patient import SYNTHETIC_PATIENT, SYNTHETIC_PATIENTS, get_patient, register_patient
from .prescreen import drug_signals, patient_screen_facts, screen_trial
from .tcga import build_case_from_tcga
from .trials import fetch_all_recruiting, fetch_glioma_trials, fetch_trial

app = FastAPI(title="Glioma Copilot API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    # Allow any Vercel deployment (prod + preview) without hardcoding the URL,
    # plus any localhost / 127.0.0.1 port for local dev — Next.js picks 3001+ when
    # 3000 is taken, which would otherwise be CORS-blocked and show "0 patients".
    allow_origin_regex=r"https://.*\.vercel\.app|http://localhost:\d+|http://127\.0\.0\.1:\d+",
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
    """List the synthetic demo cases (spanning the glioma spectrum).

    Reports are small static strings, so we return them inline — the frontend
    caches the full set and case-switching is instant (no per-switch fetch).
    """
    return {"patients": [
        {"id": p["id"], "label": p["label"], "report": p["report"],
         "provenance": p.get("provenance")}
        for p in SYNTHETIC_PATIENTS
    ]}


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


@app.get("/api/evidence")
def evidence(diagnosis: str | None = None, nct_id: str | None = None, markers: str | None = None):
    """Cited evidence layer for a patient (diagnosis + markers) and/or trial (nct_id).

    Generated by Claude Science and PubMed-verified (see app/evidence.py). Returns only
    the briefs relevant to the query so the Investigation view can attach grounded,
    clickable sources to its claims. `markers` is comma-separated profile keys.
    """
    marker_list = [m for m in (markers or "").split(",") if m.strip()] or None
    return evidence_lookup(diagnosis=diagnosis, nct_id=nct_id, markers=marker_list)


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


_FIT_STREAM_SYSTEM = _FIT_SYSTEM.rsplit("Return STRICT JSON only:", 1)[0] + (
    "Output each criterion as a STANDALONE JSON object, ONE PER LINE (JSONL) — no "
    "wrapping array or object, no code fences, no prose, no line breaks inside an "
    "object. Each line exactly:\n"
    '{"criterion": "", "kind": "inclusion|exclusion", "verdict": "met|not_met|unknown", '
    '"citation": "<exact eligibility line>", "rationale": "<short, what in the report decided it>"}'
)


def _extract_objects(buf: str) -> tuple[list[str], str]:
    """Pull complete top-level {...} JSON objects from a streaming buffer.

    Returns (complete object strings, remaining buffer). Robust to newlines,
    commas, and array brackets between objects.
    """
    objs: list[str] = []
    depth = 0
    start = -1
    in_str = False
    esc = False
    for i, ch in enumerate(buf):
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            if depth > 0:
                depth -= 1
                if depth == 0 and start >= 0:
                    objs.append(buf[start : i + 1])
                    start = -1
    remaining = buf[start:] if depth > 0 and start >= 0 else ""
    return objs, remaining


@app.post("/api/fit/stream")
def fit_stream(req: FitRequest):
    """Streaming per-criterion fit — emits one NDJSON line per criterion as it lands."""
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

    def gen():
        trial_meta = {"nct_id": trial["nct_id"], "title": trial["title"],
                      "url": trial["url"], "locations": trial["locations"]}
        yield json.dumps({"type": "start", "model": model, "trial": trial_meta}) + "\n"

        items: list[dict] = []
        summary = {"met": 0, "not_met": 0, "unknown": 0}
        buffer = ""
        stream_kwargs = dict(
            model=model, max_tokens=8000, system=_FIT_STREAM_SYSTEM,
            messages=[{"role": "user", "content": user}],
            **tuning_for("fit"),  # adaptive thinking + low effort -> fast first token
        )
        try:
            with client.messages.stream(**stream_kwargs) as stream:
                for text in stream.text_stream:
                    buffer += text
                    complete, buffer = _extract_objects(buffer)
                    for obj_str in complete:
                        try:
                            item = json.loads(obj_str)
                        except json.JSONDecodeError:
                            continue
                        if not isinstance(item, dict) or "verdict" not in item:
                            continue
                        items.append(item)
                        if item["verdict"] in summary:
                            summary[item["verdict"]] += 1
                        yield json.dumps({"type": "item", "item": item}) + "\n"
        except Exception as e:
            yield json.dumps({"type": "error", "detail": str(e)}) + "\n"

        try:
            upsert_patient(patient)
            upsert_trials([trial])
            store_eligibility_results(patient["id"], trial["nct_id"], items)
        except Exception as e:
            print(f"[fit_stream] store skipped: {e}")

        yield json.dumps({"type": "summary", "summary": summary}) + "\n"

    return StreamingResponse(gen(), media_type="application/x-ndjson")


# --- Day-5 prep: proactive fit triage across the top candidate trials ---

def _summarize_items(items: list[dict]) -> dict:
    summary = {"met": 0, "not_met": 0, "unknown": 0}
    for it in items:
        if it.get("verdict") in summary:
            summary[it["verdict"]] += 1
    return summary


def _triage_signal(summary: dict) -> str:
    """A conservative triage label for clinician review — NOT a recommendation.

    A hard conflict (any not_met) outranks missing data (unknown); only a trial
    with neither reads as 'looks eligible, pending clinician confirmation'.
    """
    if summary.get("not_met", 0) > 0:
        return "conflict"
    if summary.get("unknown", 0) > 0:
        return "needs_workup"
    return "looks_eligible"


class TriageRequest(BaseModel):
    patient_id: str | None = None
    condition: str = "glioma"
    limit: int = 4  # trials to DEEP-fit (Stage 2); capped below to bound cost/latency


@app.post("/api/triage/stream")
def triage_stream(req: TriageRequest):
    """Exhaustive candidate triage, streamed. Three transparent stages:

    Stage 0 — pull EVERY recruiting trial for the tumor type (no top-N slice), so
              a relevant trial buried in the default sort is never silently missed.
    Stage 1 — a cheap, deterministic, recall-preserving pre-screen flags HARD
              conflicts with the patient's known facts (only deprioritizes, never
              hides; every flag carries a reason).
    Stage 2 — the REAL per-criterion fit (Claude) on the top `limit` screen-clear
              trials, streamed with badges. Everything else stays listed &
              openable; we report "deep-assessed N of <total>" (no silent cap).

    This stays inside the "not a trial finder" line: candidate scoping is the
    tumor type, ranking is transparent (screen + cited fit), the clinician decides.
    """
    patient = get_patient(req.patient_id)
    n = max(1, min(req.limit, 5))  # cap 1..5 deep fits to bound Claude calls (~15s each)
    facts = patient_screen_facts(patient)
    # Ground the patient's REAL prior therapies (GDC) in RxNorm+ChEMBL, so the screen
    # can match a trial that excludes a drug CLASS (e.g. 'anti-VEGF'), not just a name.
    prior_agents = ((patient.get("provenance") or {}).get("treatment") or {}).get("agents", [])
    prior_drugs = [_normalize_cached(a) for a in prior_agents if "radiation" not in a.lower()]
    drug_sigs = drug_signals(prior_drugs)
    try:
        pool = fetch_all_recruiting(condition=req.condition or "glioma")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"ClinicalTrials.gov error: {e}")

    def gen():
        # Stage 0: announce the full bounded pool.
        yield json.dumps({"type": "pool", "condition": req.condition,
                          "total": len(pool)}) + "\n"

        # Stage 1: deterministic screen over the WHOLE pool (fast, no Claude).
        screened = []
        for t in pool:
            sc = screen_trial(facts, t.get("eligibility") or "", drug_sigs)
            screened.append((t, sc))
        clear = [t for t, sc in screened if sc["status"] == "clear"]
        flagged_n = len(screened) - len(clear)
        # The ChEMBL win: trials excluding a drug CLASS a name-only filter would miss.
        mech_hits = [(t, sc) for t, sc in screened if sc.get("via_mechanism")]
        yield json.dumps({
            "type": "screen",
            "facts": facts,
            "clear": len(clear),
            "flagged": flagged_n,
            "mechanism_matched": len(mech_hits),
            "mechanism_examples": [
                {"nct_id": t["nct_id"], "reason": sc["reasons"][-1]}
                for t, sc in mech_hits[:4]
            ],
            "trials": [
                {"nct_id": t["nct_id"], "title": t["title"], "url": t["url"],
                 "locations": t["locations"], "phases": t.get("phases", []),
                 "states": t.get("states", []), "screen": sc}
                for t, sc in screened
            ],
        }) + "\n"

        try:
            upsert_patient(patient)
        except Exception as e:
            print(f"[triage] patient store skipped: {e}")

        # Stage 2: deep per-criterion fit on the top N screen-CLEAR trials. Run the
        # (up to n) Claude fit calls CONCURRENTLY and stream each as it lands, so the
        # wall-clock is ~one fit instead of the sum. DB writes stay on this generator
        # thread (only the Claude call is parallelized). Streamed in completion order;
        # the client sorts by fit anyway.
        deep = [t for t in clear if t.get("eligibility")][:n]
        meta_by_nct = {
            t["nct_id"]: {"nct_id": t["nct_id"], "title": t["title"],
                          "url": t["url"], "locations": t["locations"],
                          "phases": t.get("phases", []), "states": t.get("states", [])}
            for t in deep
        }
        if deep:
            with ThreadPoolExecutor(max_workers=len(deep)) as ex:
                futures = {ex.submit(_compute_fit_items, patient, t): t for t in deep}
                for fut in as_completed(futures):
                    t = futures[fut]
                    meta = meta_by_nct[t["nct_id"]]
                    try:
                        items = fut.result()
                    except Exception as e:
                        yield json.dumps({"type": "triage", "trial": meta, "error": str(e)}) + "\n"
                        continue
                    summary = _summarize_items(items)
                    try:
                        upsert_trials([t])
                        store_eligibility_results(patient["id"], t["nct_id"], items)
                    except Exception as e:
                        print(f"[triage] fit store skipped: {e}")
                    yield json.dumps({"type": "triage", "trial": meta, "items": items,
                                      "summary": summary,
                                      "signal": _triage_signal(summary)}) + "\n"

        yield json.dumps({"type": "done", "deep_assessed": len(deep),
                          "total": len(pool)}) + "\n"

    return StreamingResponse(gen(), media_type="application/x-ndjson")


# --- Day 4: three-agent verification loop (draft -> verify -> investigate) ---

_DRAFT_SYSTEM = (
    "You are the DRAFTING agent summarizing a trial for a busy tumor board. Given a "
    "patient and a trial's per-criterion fit assessment, write a concise evidence "
    "brief. LEAD with a clear, decisive one-line eligibility verdict (e.g. 'The "
    "patient is eligible for this trial' / 'appears eligible' / 'is not eligible'), "
    "the way a clinician would open a summary — then 3-6 supporting claims, each "
    "citing the criterion it rests on.\n\n"
    "Return STRICT JSON only:\n"
    '{"assessment": "<decisive one-line verdict>", "claims": [{"claim": "", "citation": ""}]}'
)

_VERIFY_SYSTEM = (
    "You are the VERIFICATION agent. Claude is NOT the source of truth — the "
    "per-criterion FIT ASSESSMENT is. Check EVERY claim in the draft brief against "
    "it. For each claim assign a status:\n"
    "  - \"supported\": fully backed by 'met' criteria.\n"
    "  - \"overstated\": asserts more certainty than the evidence — e.g. claims or "
    "implies eligibility while relevant criteria are 'unknown'.\n"
    "  - \"unsupported\": contradicted by a 'not_met' criterion.\n"
    "For overstated/unsupported claims, REWRITE them to match the evidence (e.g. "
    "'eligible for the trial' -> 'possibly relevant; requires EGFR testing to "
    "confirm'). Give a short reason citing the criterion.\n\n"
    "GROUNDING RULE (do NOT manufacture doubt): you may only downgrade a claim to "
    "'overstated' or 'unsupported' if you can point to a SPECIFIC criterion in the FIT "
    "ASSESSMENT that is 'unknown' (for overstated) or 'not_met' (for unsupported). Put "
    "that exact criterion text in `evidence_line`. If every relevant criterion is 'met', "
    "the claim is 'supported' — do not soften an eligible verdict without a concrete "
    "unknown/not_met line. Never turn a 'met' criterion into a doubt. (Softening the "
    "OVERALL verdict to 'confirm with the trial coordinator' is fine ONLY when driven by "
    "a real unknown/not_met line — final enrollment is never asserted, but doubt must be "
    "evidence-backed, not invented.)\n\n"
    "Return STRICT JSON only:\n"
    '{"log": [{"claim": "", "status": "supported|overstated|unsupported", '
    '"rewrite": "<corrected claim, or same text if supported>", '
    '"evidence_line": "<exact unknown/not_met criterion this rests on, or empty if supported>", '
    '"reason": ""}]}'
)

_INVESTIGATE_SYSTEM = (
    "You are the INVESTIGATION agent. Given the unknown/flagged items, list the "
    "concrete next steps to resolve each (test to order, info to obtain, who to "
    "contact). Be specific and clinical.\n\n"
    "Return STRICT JSON only:\n"
    '{"steps": [{"item": "", "action": ""}]}'
)


def _agent_json(agent: str, system: str, user: str, max_tokens: int = 4000):
    """One structured agent call -> parsed JSON (or None).

    max_tokens must cover BOTH the visible JSON and (with adaptive thinking) the
    thinking tokens — deep-reasoning agents over long inputs need a larger budget
    or the JSON truncates mid-object and fails to parse.
    """
    msg = client.messages.create(
        model=model_for(agent), max_tokens=max_tokens, system=system,
        messages=[{"role": "user", "content": user}], **tuning_for(agent),
    )
    return parse_json(text_from(msg))


def _compute_fit_items(patient: dict, trial: dict) -> list[dict]:
    """Run the fit assessment once (non-streaming) and return its items."""
    user = (
        f"PATIENT REPORT:\n{patient['report']}\n\n"
        f"TRIAL {trial['nct_id']} — {trial['title']}\n"
        f"ELIGIBILITY CRITERIA:\n{trial['eligibility']}"
    )
    msg = client.messages.create(
        model=model_for("fit"), max_tokens=8000, system=_FIT_SYSTEM,
        messages=[{"role": "user", "content": user}], **tuning_for("fit"),
    )
    parsed = parse_json(text_from(msg)) or {}
    return parsed.get("items", [])


def _norm_tokens(s: str) -> set[str]:
    return {t for t in re.sub(r"[^a-z0-9 ]", " ", (s or "").lower()).split() if len(t) > 2}


def _enforce_evidence_grounding(verify: dict, items: list[dict]) -> dict:
    """Hard guardrail so verify can't manufacture doubt.

    A downgrade to 'overstated'/'unsupported' is kept only if its `evidence_line`
    actually overlaps a criterion of the matching verdict ('unknown' / 'not_met') in
    the fit table (the source of truth). A flag grounded in nothing real is reverted to
    'supported' — the symmetric partner to "don't fake a catch": don't fake a doubt.
    """
    verdict_tokens = {"unknown": [], "not_met": []}
    for it in items:
        v = it.get("verdict")
        if v in verdict_tokens:
            verdict_tokens[v].append(_norm_tokens(it.get("criterion", "")))
    need = {"overstated": "unknown", "unsupported": "not_met"}
    for e in verify.get("log", []):
        status = e.get("status")
        if status not in need:
            continue
        pools = verdict_tokens[need[status]]
        line = _norm_tokens(e.get("evidence_line", ""))
        grounded = bool(line) and any(
            len(line & pool) >= max(2, min(len(line), len(pool)) // 3) for pool in pools
        )
        if not grounded:
            e["status"] = "supported"
            e["rewrite"] = e.get("claim", e.get("rewrite", ""))
            e["reason"] = "(doubt dropped: not backed by an unknown/not_met line in the fit table)"
            e["evidence_line"] = ""
            e["grounding_reverted"] = True
    return verify


def _fit_digest(items: list[dict]) -> str:
    lines = [
        f"- [{it.get('verdict')}] ({it.get('kind')}) {it.get('criterion')}"
        f"  | cite: {it.get('citation')}"
        for it in items
    ]
    return "\n".join(lines)


@app.post("/api/review/stream")
def review_stream(req: FitRequest):
    """Three-agent loop: draft -> verify (catch overclaims) -> investigate, streamed."""
    patient = get_patient(req.patient_id)
    trial = fetch_trial(req.nct_id)
    if trial is None:
        raise HTTPException(status_code=404, detail=f"Trial {req.nct_id} not found")

    def gen():
        # Reuse stored fit verdicts if present; otherwise compute them now.
        try:
            items = get_eligibility_results(patient["id"], trial["nct_id"])
        except Exception:
            items = []
        if not items:
            yield json.dumps({"type": "stage", "stage": "fit"}) + "\n"
            items = _compute_fit_items(patient, trial)
        digest = _fit_digest(items)
        trial_meta = {"nct_id": trial["nct_id"], "title": trial["title"]}
        yield json.dumps({"type": "trial", "trial": trial_meta}) + "\n"

        # 1) Drafting agent
        yield json.dumps({"type": "stage", "stage": "draft"}) + "\n"
        draft = _agent_json(
            "draft", _DRAFT_SYSTEM,
            f"PATIENT: {patient['label']}\n\nFIT ASSESSMENT:\n{digest}",
        ) or {"assessment": "", "claims": []}
        yield json.dumps({"type": "draft", "draft": draft}) + "\n"

        # 2) Verification agent — the money moment. Fold the headline verdict in as
        # the first claim so it gets scrutinized hardest.
        yield json.dumps({"type": "stage", "stage": "verify"}) + "\n"
        claims_to_check = [
            {"claim": draft.get("assessment", ""), "citation": "overall verdict"}
        ] + draft.get("claims", [])
        verify = _agent_json(
            "verify", _VERIFY_SYSTEM,
            "CLAIMS TO VERIFY (the FIRST is the overall eligibility verdict — "
            f"scrutinize it hardest):\n{json.dumps(claims_to_check)}\n\n"
            f"FIT ASSESSMENT (source of truth):\n{digest}",
        ) or {"log": []}
        # Hard guardrail: a downgrade must cite a real unknown/not_met line, else revert.
        verify = _enforce_evidence_grounding(verify, items)
        yield json.dumps({"type": "verify", "verify": verify}) + "\n"

        # 3) Investigation agent
        yield json.dumps({"type": "stage", "stage": "investigate"}) + "\n"
        unknowns = _fit_digest([it for it in items if it.get("verdict") == "unknown"])
        flagged = [e for e in verify.get("log", []) if e.get("status") != "supported"]
        investigate = _agent_json(
            "investigate", _INVESTIGATE_SYSTEM,
            f"UNKNOWN CRITERIA:\n{unknowns}\n\nFLAGGED CLAIMS:\n{json.dumps(flagged)}",
        ) or {"steps": []}
        yield json.dumps({"type": "investigate", "investigate": investigate}) + "\n"

        yield json.dumps({"type": "done"}) + "\n"

    return StreamingResponse(gen(), media_type="application/x-ndjson")


# --- Day 6: independent clinician audit (adversarial cross-check of the fit table) ---
#
# This is NOT the verify agent. Verify takes the fit table as ground truth and only
# checks the draft for overclaiming. The AUDIT agent challenges the fit table ITSELF:
# it re-judges each eligibility criterion from scratch, as an independent board-certified
# neuro-oncologist grounded in WHO CNS5 — WITHOUT seeing our system's reasoning — then is
# shown our verdicts only to flag disagreements. Different model (Opus) decorrelates its
# errors from the Sonnet fit drafter. It catches inconsistency + misreads; it CANNOT catch
# shared blind spots (both models mis-reading the same line the same way) — a real human is
# still needed for that. NEVER label its output "clinician-validated".

_AUDIT_INDEPENDENT_SYSTEM = (
    "You are an INDEPENDENT board-certified neuro-oncologist auditing a clinical-trial "
    "eligibility screen. You are given ONLY a patient's pathology/clinical report and a "
    "trial's raw eligibility criteria. Judge the patient against each decision-relevant "
    "criterion FROM SCRATCH, using your own clinical reasoning grounded in the WHO CNS5 "
    "(2021) classification and standard neuro-oncology practice. You have NOT seen any "
    "other system's answer — form your own.\n\n"
    "For each criterion assign a VERDICT (patient's compatibility with enrolling on that "
    "line):\n"
    "  - \"met\": patient satisfies it (for an EXCLUSION, means the patient does NOT have "
    "the excluding condition — handle negation carefully).\n"
    "  - \"not_met\": patient clearly fails/violates it.\n"
    "  - \"unknown\": the report does not contain the needed fact; say what test/info is "
    "required. Do NOT assume unstated facts.\n\n"
    "Quote the exact eligibility line in `citation`. Return STRICT JSON only:\n"
    "{\n"
    '  "items": [\n'
    '    {"criterion": "", "kind": "inclusion|exclusion", "verdict": "met|not_met|unknown", '
    '"citation": "<exact eligibility line>", "rationale": "<your clinical reasoning>"}\n'
    "  ]\n"
    "}"
)

_AUDIT_COMPARE_SYSTEM = (
    "You are an INDEPENDENT neuro-oncologist reviewer comparing YOUR OWN eligibility "
    "verdicts (done blind) against the verdicts a screening system produced for the SAME "
    "patient and trial. Your job is adversarial: surface every place the system may have "
    "gotten it wrong. Match criteria by meaning, not wording.\n\n"
    "For each of YOUR criteria, decide agreement with the system's verdict on the same "
    "criterion:\n"
    "  - \"agree\": same verdict (met/not_met/unknown).\n"
    "  - \"disagree\": different verdict — state which is clinically correct and why, "
    "citing the criterion + the WHO CNS5 / trial rule that decides it.\n"
    "  - \"system_missing\": a decision-relevant criterion YOU judged that the system did "
    "not assess at all.\n"
    "Be fair: if the system is right, say 'agree' — do not manufacture disagreement.\n\n"
    "Return STRICT JSON only:\n"
    "{\n"
    '  "comparisons": [\n'
    '    {"criterion": "", "your_verdict": "met|not_met|unknown", '
    '"system_verdict": "met|not_met|unknown|absent", '
    '"status": "agree|disagree|system_missing", '
    '"correct_verdict": "<the clinically correct verdict>", '
    '"reason": "<why, citing the rule>"}\n'
    "  ],\n"
    '  "verdict": "<one-line overall: does the system\'s eligibility screen hold up?>"\n'
    "}"
)


def _audit_scores(comparisons: list[dict]) -> dict:
    """Agreement rate + counts over the audit comparisons."""
    total = agree = disagree = missing = 0
    for c in comparisons:
        st = c.get("status")
        if st == "agree":
            agree += 1
            total += 1
        elif st == "disagree":
            disagree += 1
            total += 1
        elif st == "system_missing":
            missing += 1
    rate = round(agree / total, 3) if total else None
    return {
        "agreement_rate": rate,
        "agree": agree,
        "disagree": disagree,
        "system_missing": missing,
        "compared": total,
    }


@app.post("/api/audit/stream")
def audit_stream(req: FitRequest):
    """Independent clinician audit: blind re-derivation -> compare to our fit table.

    An adversarial cross-check that challenges the fit verdicts themselves (unlike
    verify, which trusts them). NOT clinician validation — it cannot catch blind spots
    both models share; a human reviewer is still required.
    """
    patient = get_patient(req.patient_id)
    trial = fetch_trial(req.nct_id)
    if trial is None:
        raise HTTPException(status_code=404, detail=f"Trial {req.nct_id} not found")
    if not trial.get("eligibility"):
        raise HTTPException(status_code=422, detail="Trial has no eligibility text")

    def gen():
        trial_meta = {"nct_id": trial["nct_id"], "title": trial["title"], "url": trial["url"]}
        yield json.dumps({"type": "trial", "trial": trial_meta}) + "\n"

        # Our system's verdicts (reuse if stored, else compute).
        try:
            system_items = get_eligibility_results(patient["id"], trial["nct_id"])
        except Exception:
            system_items = []
        if not system_items:
            yield json.dumps({"type": "stage", "stage": "fit"}) + "\n"
            system_items = _compute_fit_items(patient, trial)

        # 1) BLIND independent re-derivation — the auditor never sees system_items here.
        yield json.dumps({"type": "stage", "stage": "independent"}) + "\n"
        indep = _agent_json(
            "audit", _AUDIT_INDEPENDENT_SYSTEM,
            f"PATIENT REPORT:\n{patient['report']}\n\n"
            f"TRIAL {trial['nct_id']} — {trial['title']}\n"
            f"ELIGIBILITY CRITERIA:\n{trial['eligibility']}",
            max_tokens=12000,
        ) or {"items": []}
        indep_items = indep.get("items", [])
        yield json.dumps({"type": "independent", "items": indep_items}) + "\n"

        # 2) Compare — only now is the auditor shown our verdicts.
        yield json.dumps({"type": "stage", "stage": "compare"}) + "\n"
        compare = _agent_json(
            "audit", _AUDIT_COMPARE_SYSTEM,
            f"YOUR INDEPENDENT VERDICTS:\n{_fit_digest(indep_items)}\n\n"
            f"SYSTEM VERDICTS (to audit):\n{_fit_digest(system_items)}",
            max_tokens=12000,
        ) or {"comparisons": [], "verdict": ""}
        comparisons = compare.get("comparisons", [])
        scores = _audit_scores(comparisons)
        yield json.dumps({
            "type": "audit",
            "comparisons": comparisons,
            "scores": scores,
            "verdict": compare.get("verdict", ""),
            "disclaimer": (
                "Automated independent AI cross-check (Opus, blind re-derivation). "
                "Catches inconsistencies and misreads; cannot catch blind spots both "
                "models share. NOT clinician validation."
            ),
        }) + "\n"
        yield json.dumps({"type": "done"}) + "\n"

    return StreamingResponse(gen(), media_type="application/x-ndjson")


# --- Day 5: shared-decision workspace (plain-language + preferences + summary) ---

_EXPLAIN_SYSTEM = (
    "You are the PLAIN-LANGUAGE agent, rendering a trial's clinician-facing fit "
    "assessment for the PATIENT and family, doctor-guided. Write at a ~7th-grade "
    "reading level, warm and clear, no jargon (briefly define any unavoidable term). "
    "Ground the patient-SPECIFIC parts (what_it_is, why_it_may_fit, open_questions, "
    "what_it_involves) ONLY in the FIT ASSESSMENT provided — do NOT invent facts about "
    "this patient.\n\n"
    "HONESTY RULES (critical): do NOT tell the patient they ARE eligible or that the "
    "trial will help. 'unknown' criteria are OPEN QUESTIONS to confirm with the care "
    "team, not reassurances. This is an explanation for a conversation with their "
    "doctor, NOT medical advice or a recommendation.\n\n"
    "PROGNOSIS RED LINE: never estimate how long the patient may live, their odds, or "
    "individual prognosis — that belongs to the treating clinician alone. If survival "
    "comes up, redirect it to the doctor.\n\n"
    "COMMON QUESTIONS: neuro-oncology patients and families reliably get lost on the "
    "same handful of things (list curated from a neuro-oncology clinician's real patient "
    "group). WHERE RELEVANT TO THIS TRIAL, add short, GENERAL, educational answers "
    "(glossary-style, NOT claims about this patient) drawn from this list:\n"
    "  - Trial design & arms: what randomization / a control (placebo) arm means; that a "
    "control arm still receives standard care ('no added harm') and is typically offered "
    "the study drug later.\n"
    "  - Trial terms IF they appear in the criteria: Phase 1/2/3, PR (partial response), "
    "CR (complete response), OS (overall survival), PFS (progression-free survival), RANO.\n"
    "  - Resection levels: biopsy vs partial vs gross-total vs supratotal/FLAIR — and that "
    "an early post-op MRI, not the surgeon's impression, defines the extent.\n"
    "  - What happens if the disease recurs while on the trial.\n"
    "  - Life on a trial: the fixed MRI / blood-draw schedule and reduced travel freedom.\n"
    "  - That trials are not only drugs (also devices like Tumor Treating Fields, cell / "
    "immune therapy, diet studies) — so other kinds of options exist beyond this one.\n"
    "  - Reasons a participant may have to withdraw (e.g. pregnancy, moving away).\n"
    "Include only the 2-4 items that actually fit THIS trial; never dump the whole list, "
    "and never answer 'how long will I live' — redirect to the doctor.\n\n"
    "Return STRICT JSON only:\n"
    "{\n"
    '  "what_it_is": "<1-2 plain sentences: what this trial is studying>",\n'
    '  "why_it_may_fit": "<what already lines up for this patient, from met criteria>",\n'
    '  "open_questions": ["<each unknown as a question to ask the care team>"],\n'
    '  "what_it_involves": "<plain note on visits/logistics IF stated; else omit specifics>",\n'
    '  "common_questions": [{"q": "<a question patients commonly ask that is relevant here>", "plain_answer": "<short, general, educational answer; not specific to this patient; no prognosis>"}],\n'
    '  "questions_to_ask": ["<2-4 good questions for the patient to ask their doctor>"]\n'
    "}"
)


@app.post("/api/explain")
def explain(req: FitRequest):
    """Plain-language rendering of a trial's verified fit, for the patient."""
    patient = get_patient(req.patient_id)
    trial = fetch_trial(req.nct_id)
    if trial is None:
        raise HTTPException(status_code=404, detail=f"Trial {req.nct_id} not found")

    try:
        items = get_eligibility_results(patient["id"], trial["nct_id"])
    except Exception:
        items = []
    if not items:
        items = _compute_fit_items(patient, trial)

    parsed = _agent_json(
        "explain", _EXPLAIN_SYSTEM,
        f"TRIAL {trial['nct_id']} — {trial['title']}\n\n"
        f"PER-CRITERION FIT ASSESSMENT (source of truth):\n{_fit_digest(items)}",
    ) or {}
    return {
        "trial": {"nct_id": trial["nct_id"], "title": trial["title"], "url": trial["url"]},
        "explanation": parsed,
    }


class Preferences(BaseModel):
    travel: str = "unsure"          # in_state | regional | anywhere | unsure
    home_state: str | None = None   # patient's US state (for the travel heuristic)
    goal: str = "unsure"            # quality_of_life | balanced | aggressive | unsure
    phase1: str = "unsure"          # avoid | open | unsure (earliest-phase wariness)
    caregiver: str = "unsure"       # strong | limited | unsure
    financial_concern: bool = False


class SummaryCandidate(BaseModel):
    nct_id: str
    title: str
    url: str | None = None
    signal: str = "needs_workup"
    summary: dict = {}
    phases: list[str] = []
    states: list[str] = []


class SummaryRequest(BaseModel):
    patient_id: str | None = None
    preferences: Preferences
    candidates: list[SummaryCandidate]


def _is_earliest_phase(phases: list[str]) -> bool:
    return any(p in ("PHASE1", "EARLY_PHASE1") for p in (phases or []))


def _preference_rerank(prefs: Preferences, candidates: list[SummaryCandidate]) -> list[dict]:
    """DETERMINISTIC, documented re-rank by fit + preferences — NOT a recommendation.

    Every adjustment carries a human-readable reason so the re-ordering is fully
    transparent and clinician/patient-overridable. Preferences only re-weight the
    already-assessed candidates; they never add or discover trials.
    """
    base_by_signal = {"looks_eligible": 100, "needs_workup": 60, "conflict": 20}
    ranked = []
    for c in candidates:
        s = c.summary or {}
        base = base_by_signal.get(c.signal, 50)
        base -= 2 * int(s.get("unknown", 0)) + 10 * int(s.get("not_met", 0))
        adjustments: list[dict] = []

        earliest = _is_earliest_phase(c.phases)
        in_state = bool(prefs.home_state and prefs.home_state in (c.states or []))

        # Travel
        if prefs.travel == "in_state" and prefs.home_state:
            if in_state:
                adjustments.append({"delta": 10, "reason": f"Has a site in your state ({prefs.home_state})."})
            else:
                adjustments.append({"delta": -25, "reason": f"No site listed in your state ({prefs.home_state}); would require out-of-state travel."})
        elif prefs.travel == "regional" and prefs.home_state and not in_state:
            adjustments.append({"delta": -10, "reason": "No nearby site; some travel likely."})

        # Earliest-phase wariness / openness
        if earliest and prefs.phase1 == "avoid":
            adjustments.append({"delta": -20, "reason": "This is an earliest-phase (Phase 1) study, which you preferred to avoid."})
        elif earliest and prefs.phase1 == "open":
            adjustments.append({"delta": 5, "reason": "Earliest-phase study; you said you're open to these."})

        # Goal alignment
        if earliest and prefs.goal == "quality_of_life":
            adjustments.append({"delta": -10, "reason": "Experimental/early-phase; you prioritized quality of life."})
        elif earliest and prefs.goal == "aggressive":
            adjustments.append({"delta": 10, "reason": "Experimental/early-phase; matches your interest in aggressive options."})

        score = base + sum(a["delta"] for a in adjustments)
        ranked.append({
            "nct_id": c.nct_id, "title": c.title, "url": c.url,
            "signal": c.signal, "summary": s, "phases": c.phases,
            "base": base, "adjustments": adjustments, "score": score,
        })
    ranked.sort(key=lambda r: r["score"], reverse=True)
    return ranked


_SUMMARY_SYSTEM = (
    "You are the SHARED-DECISION agent writing a note for a patient + clinician to "
    "discuss together. You are given a DETERMINISTIC ranked list of trials (already "
    "assessed for fit and re-weighted by the patient's stated preferences, with the "
    "reason for each adjustment) plus the raw preferences. Write a short, plain, "
    "non-directive note.\n\n"
    "HONESTY RULES: do NOT recommend a trial or say one is 'best'. Explain how the "
    "patient's preferences shifted the ordering, note trade-offs, and frame everything "
    "as points for discussion with the care team. Not medical advice.\n\n"
    "Return STRICT JSON only:\n"
    "{\n"
    '  "note": "<3-5 plain sentences summarizing the options in light of preferences>",\n'
    '  "discussion_points": ["<specific trade-off or question to raise with the care team>"]\n'
    "}"
)


@app.post("/api/summary")
def summary(req: SummaryRequest):
    """Shared-decision summary: deterministic preference re-rank + plain narrative."""
    ranked = _preference_rerank(req.preferences, req.candidates)
    prefs = req.preferences.model_dump()
    digest = "\n".join(
        f"- {r['title']} ({r['nct_id']}) — signal={r['signal']}, score={r['score']} "
        f"[{'; '.join(a['reason'] for a in r['adjustments']) or 'no preference adjustment'}]"
        for r in ranked
    )
    note = _agent_json(
        "summary", _SUMMARY_SYSTEM,
        f"PATIENT PREFERENCES:\n{json.dumps(prefs)}\n\n"
        f"RANKED CANDIDATES (deterministic, preference-weighted):\n{digest}",
    ) or {"note": "", "discussion_points": []}
    return {"ranked": ranked, "preferences": prefs, "note": note}


# --- Drug-name normalization: Claude extracts -> RxNorm + ChEMBL ground it ---

def _normalize_cached(name: str) -> dict:
    """Normalize one drug via Postgres cache, else live RxNorm+ChEMBL then persist."""
    key = (name or "").strip().lower()
    if not key:
        return normalize_drug(name)
    try:
        cached = get_drug_cache(key)
        if cached:
            return cached
    except Exception as e:
        print(f"[drugs] cache read skipped: {e}")
    result = normalize_drug(name)
    try:
        put_drug_cache(key, result)
    except Exception as e:
        print(f"[drugs] cache write skipped: {e}")
    return result


class DrugNormalizeRequest(BaseModel):
    names: list[str]


@app.post("/api/drugs/normalize")
def drugs_normalize(req: DrugNormalizeRequest):
    """Normalize a list of drug mentions to canonical RxNorm + ChEMBL identities."""
    seen: set[str] = set()
    out = []
    for n in req.names:
        k = (n or "").strip().lower()
        if not k or k in seen:
            continue
        seen.add(k)
        out.append(_normalize_cached(n))
    return {"drugs": out}


_DRUG_EXTRACT_SYSTEM = (
    "List the DISTINCT drug / therapy names mentioned as treatments the patient has "
    "received in this report. Report ONLY drug names actually present (generic or brand), "
    "one canonical token each — no doses, no regimen names. Return STRICT JSON only:\n"
    '{"drugs": ["temozolomide", "bevacizumab"]}'
)


class TcgaRequest(BaseModel):
    barcode: str


@app.post("/api/case/from_tcga")
def case_from_tcga(req: TcgaRequest):
    """Live-load a case from a real de-identified TCGA barcode (cBioPortal + GDC).

    Proves real-time analysis on real data: a reviewer drops in any TCGA glioma
    barcode and the whole pipeline runs on it. Survival is never fetched/shown.
    """
    try:
        case = build_case_from_tcga(req.barcode)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"TCGA fetch error: {e}")
    register_patient(case)  # so fit/triage/review/drugs can look it up by id
    return {"id": case["id"], "label": case["label"], "report": case["report"],
            "provenance": case["provenance"]}


@app.post("/api/drugs/from_patient")
def drugs_from_patient(req: ExtractRequest):
    """Extract drug mentions from a patient report (Claude), then normalize each.

    The demoable groundedness beat: Claude only NAMES the drugs; RxNorm + ChEMBL
    resolve identity + mechanism authoritatively.
    """
    report = req.report or SYNTHETIC_PATIENT["report"]
    parsed = _agent_json("extract", _DRUG_EXTRACT_SYSTEM, report) or {}
    names = [n for n in (parsed.get("drugs") or []) if isinstance(n, str)]
    drugs = [_normalize_cached(n) for n in dict.fromkeys(n.strip().lower() for n in names if n.strip())]
    return {"mentions": names, "drugs": drugs}
