"""Stage 1 — cheap, deterministic, recall-preserving pre-screen.

No Claude here. We scan each trial's eligibility text for HARD conflicts with the
patient's known structured facts (molecular type, prior bevacizumab), and only
DEPRIORITIZE flagged trials — we never hide them. Every flag carries a reason and
cites the direction of the conflict, so the clinician can override, and the
downstream per-criterion fit (Stage 2) remains the real arbiter.

Precision note: to reduce false positives we split eligibility into its
Inclusion vs Exclusion sections and screen each for the right kind of signal
(a required biomarker in Inclusion; a prior-therapy restriction in Exclusion).
This is a keyword aid, not proof — labeled as such in the UI.
"""

from typing import Any


def patient_screen_facts(patient: dict[str, Any]) -> dict[str, Any]:
    """Normalize a patient into the few structured facts the screen keys on.

    Molecular facts come from the REAL cBioPortal provenance markers; the
    clinical flags (prior bevacizumab, recurrence) come from the case's labeled
    constructed layer. All are clinician-auditable — no model judgment.
    """
    markers = (patient.get("provenance") or {}).get("markers", {})
    idh_raw = str(markers.get("IDH_STATUS", "")).lower()
    codel_raw = str(markers.get("IDH_CODEL_SUBTYPE", "")).lower()

    idh = "wildtype" if idh_raw == "wt" else "mutant" if idh_raw == "mutant" else "unknown"
    if "non-codel" in codel_raw or codel_raw == "idhwt":
        codel = "intact"
    elif "codel" in codel_raw:
        codel = "codeleted"
    else:
        codel = "unknown"

    clinical = patient.get("clinical", {})
    return {
        "idh": idh,
        "codel": codel,
        "prior_bevacizumab": bool(clinical.get("prior_bevacizumab")),
    }


def _split_eligibility(elig: str) -> tuple[str, str]:
    """Return (inclusion_text, exclusion_text), lowercased.

    If no 'exclusion' header is found, treat the whole text as inclusion.
    """
    e = (elig or "").lower()
    idx = e.find("exclusion criteria")
    if idx == -1:
        idx = e.find("exclusion")
    if idx == -1:
        return e, ""
    return e[:idx], e[idx:]


def _any(text: str, needles: list[str]) -> bool:
    return any(n in text for n in needles)


def screen_trial(facts: dict[str, Any], eligibility: str) -> dict[str, Any]:
    """Deterministic hard-conflict screen → {status: clear|flagged, reasons: [...]}"""
    inclusion, exclusion = _split_eligibility(eligibility)
    reasons: list[str] = []

    idh = facts.get("idh")
    # A required IDH type in the INCLUSION section that the patient can't meet.
    if idh == "wildtype" and _any(inclusion, ["idh-mutant", "idh mutant", "idh1 mutation",
                                              "idh-mutation", "mutant idh", "idh1/2 mutant"]):
        reasons.append("Inclusion appears to require IDH-mutant; patient is IDH-wildtype")
    if idh == "mutant" and _any(inclusion, ["idh-wildtype", "idh wild-type", "idh wildtype",
                                            "idh-wt", "wildtype idh", "idh1/2 wild-type"]):
        reasons.append("Inclusion appears to require IDH-wildtype; patient is IDH-mutant")

    # 1p/19q codeletion required in inclusion, patient non-codeleted.
    if facts.get("codel") == "intact" and _any(inclusion, ["1p/19q co-delet", "1p/19q codelet",
                                                            "1p19q co-delet", "co-deleted 1p"]):
        reasons.append("Inclusion appears to require 1p/19q-codeletion; patient is non-codeleted")

    # Prior bevacizumab / anti-VEGF restriction in the EXCLUSION section.
    if facts.get("prior_bevacizumab") and _any(exclusion, ["bevacizumab", "anti-vegf", "anti vegf",
                                                           "vegf inhibitor"]):
        reasons.append("Exclusion references prior bevacizumab / anti-VEGF; patient received bevacizumab")

    return {"status": "flagged" if reasons else "clear", "reasons": reasons}
