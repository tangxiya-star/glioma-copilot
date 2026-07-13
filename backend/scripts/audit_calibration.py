"""Calibrate the independent clinician-audit agent against known-answer cases.

The audit agent's credibility rests on agreeing with cases where WE already know the
correct verdict. This harness runs the blind re-derivation + compare flow in-process and
checks that the auditor lands on the expected verdict for the key decision criterion.

    cd backend && ../.venv/bin/python -m scripts.audit_calibration

Requires ANTHROPIC_API_KEY in the repo-root .env and network (fetches live trials).
Add pairs to CASES as you find more ground-truth (case, trial, expected-verdict) anchors.
"""

import json

from app.main import (
    _AUDIT_COMPARE_SYSTEM,
    _AUDIT_INDEPENDENT_SYSTEM,
    _agent_json,
    _audit_scores,
    _compute_fit_items,
    _fit_digest,
)
from app.patient import get_patient
from app.trials import fetch_trial

# Ground-truth anchors: (case_id, nct_id, expected verdict on the key criterion, hint).
# Case 004: recurrent GBM w/ prior bevacizumab vs a trial excluding prior anti-VEGF ->
#   the buried exclusion must resolve to not_met. Reliable Depth demo.
# Case 001: GBM IDH-wt with EGFR NOT yet tested -> an EGFR-gated criterion must be unknown.
CASES = [
    {
        "case": "case-004",
        "nct": "NCT05432804",
        "expect": "not_met",
        # Precise, low-frequency terms that identify the KEY decision line (any-match).
        "key_terms": ["bevacizumab", "anti-vegf", "vegf", "angiogen"],
        "hint": "prior bevacizumab / anti-VEGF exclusion",
    },
    # Add a known EGFR-gated trial for case-001 here once confirmed, expect "unknown".
]


def run_one(case_id: str, nct_id: str, expect: str, key_terms: list, hint: str) -> dict:
    patient = get_patient(case_id)
    trial = fetch_trial(nct_id)
    if trial is None or not trial.get("eligibility"):
        return {"case": case_id, "nct": nct_id, "error": "trial not found / no eligibility"}

    system_items = _compute_fit_items(patient, trial)

    indep = _agent_json(
        "audit", _AUDIT_INDEPENDENT_SYSTEM,
        f"PATIENT REPORT:\n{patient['report']}\n\n"
        f"TRIAL {trial['nct_id']} — {trial['title']}\n"
        f"ELIGIBILITY CRITERIA:\n{trial['eligibility']}",
        max_tokens=12000,
    ) or {"items": []}
    indep_items = indep.get("items", [])

    compare = _agent_json(
        "audit", _AUDIT_COMPARE_SYSTEM,
        f"YOUR INDEPENDENT VERDICTS:\n{_fit_digest(indep_items)}\n\n"
        f"SYSTEM VERDICTS (to audit):\n{_fit_digest(system_items)}",
        max_tokens=12000,
    ) or {"comparisons": [], "verdict": ""}
    comparisons = compare.get("comparisons", [])
    scores = _audit_scores(comparisons)

    # Did the auditor's independent verdict match the known-correct verdict on the key line?
    key = None
    for it in indep_items:
        text = f"{it.get('criterion','')} {it.get('citation','')}".lower()
        if any(term in text for term in key_terms):
            key = it
            break
    key_verdict = key.get("verdict") if key else None
    calibrated = key_verdict == expect

    disagreements = [c for c in comparisons if c.get("status") != "agree"]
    return {
        "case": case_id,
        "nct": nct_id,
        "expect_on_key": expect,
        "auditor_key_verdict": key_verdict,
        "CALIBRATED": calibrated,
        "concordance_rate": scores["concordance_rate"],
        "scores": scores,
        "overall": compare.get("verdict", ""),
        "disagreements": disagreements,
    }


def main():
    results = []
    for c in CASES:
        print(f"\n=== auditing {c['case']} vs {c['nct']} (expect {c['expect']} on: {c['hint']}) ===")
        r = run_one(c["case"], c["nct"], c["expect"], c["key_terms"], c["hint"])
        results.append(r)
        print(json.dumps(r, indent=2, ensure_ascii=False))

    passed = sum(1 for r in results if r.get("CALIBRATED"))
    print(f"\n>>> CALIBRATION: {passed}/{len(results)} anchors matched the known-correct verdict.")
    if passed < len(results):
        print(">>> A miss means EITHER the auditor OR the system is wrong on that line — inspect both.")


if __name__ == "__main__":
    main()
