"""Live ClinicalTrials.gov v2 API access — recruiting glioma trials.

No API key. We pull a page of studies and flatten the nested protocolSection
into a clean shape the frontend and downstream agents can use.
"""

from typing import Any

import requests

CTGOV_URL = "https://clinicaltrials.gov/api/v2/studies"

# Fields we ask the API to return (keeps payloads small).
_FIELDS = [
    "NCTId",
    "BriefTitle",
    "OverallStatus",
    "Phase",
    "Condition",
    "EligibilityCriteria",
    "LocationCity",
    "LocationState",
    "LocationCountry",
]


def _flatten(study: dict[str, Any]) -> dict[str, Any]:
    ps = study.get("protocolSection", {})
    ident = ps.get("identificationModule", {})
    status = ps.get("statusModule", {})
    design = ps.get("designModule", {})
    conds = ps.get("conditionsModule", {})
    elig = ps.get("eligibilityModule", {})
    locs = ps.get("contactsLocationsModule", {}).get("locations", []) or []

    cities = sorted(
        {
            ", ".join(
                p for p in (loc.get("city"), loc.get("country")) if p
            )
            for loc in locs
            if loc.get("city")
        }
    )
    # US states with a site — used by the shared-decision travel heuristic.
    states = sorted({loc.get("state") for loc in locs if loc.get("state")})

    return {
        "nct_id": ident.get("nctId"),
        "title": ident.get("briefTitle"),
        "status": status.get("overallStatus"),
        "phases": design.get("phases", []) or [],
        "conditions": conds.get("conditions", []),
        "eligibility": elig.get("eligibilityCriteria"),
        "locations": cities,
        "states": states,
        "url": f"https://clinicaltrials.gov/study/{ident.get('nctId')}",
    }


def fetch_trial(nct_id: str) -> dict[str, Any] | None:
    """Fetch a single study by NCT id (fresh eligibility text)."""
    resp = requests.get(
        f"{CTGOV_URL}/{nct_id}",
        params={"fields": ",".join(_FIELDS)},
        timeout=30,
    )
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return _flatten(resp.json())


def fetch_all_recruiting(condition: str = "glioma", max_trials: int = 1000) -> list[dict[str, Any]]:
    """Exhaustively pull EVERY recruiting trial for a condition (paginated).

    Stage 0 of candidate triage: the pool is finite and bounded, so we take ALL
    of it — no top-N slice. This guarantees a genuinely relevant trial buried in
    ClinicalTrials.gov's default sort is still in the pool (never silently
    missed); ranking is left to the transparent downstream screen + fit.
    """
    out: list[dict[str, Any]] = []
    page_token: str | None = None
    for _ in range(10):  # safety cap: 10 * 1000 = 10k, far above any glioma cond
        params = {
            "query.cond": condition or "glioma",
            "filter.overallStatus": "RECRUITING",
            "pageSize": 1000,
            "fields": ",".join(_FIELDS),
        }
        if page_token:
            params["pageToken"] = page_token
        resp = requests.get(CTGOV_URL, params=params, timeout=45)
        resp.raise_for_status()
        data = resp.json()
        out.extend(_flatten(s) for s in data.get("studies", []))
        page_token = data.get("nextPageToken")
        if not page_token or len(out) >= max_trials:
            break
    return out[:max_trials]


def fetch_glioma_trials(page_size: int = 20, condition: str = "glioma") -> list[dict[str, Any]]:
    """Pull recruiting trials for a condition, flattened.

    `condition` narrows the candidate set to the patient's tumor type
    (e.g. glioblastoma / astrocytoma / oligodendroglioma) — candidate scoping
    for clinician review, NOT autonomous discovery/recommendation.
    """
    params = {
        "query.cond": condition or "glioma",
        "filter.overallStatus": "RECRUITING",
        "pageSize": page_size,
        "fields": ",".join(_FIELDS),
    }
    resp = requests.get(CTGOV_URL, params=params, timeout=30)
    resp.raise_for_status()
    studies = resp.json().get("studies", [])
    return [_flatten(s) for s in studies]
