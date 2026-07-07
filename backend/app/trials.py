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

    return {
        "nct_id": ident.get("nctId"),
        "title": ident.get("briefTitle"),
        "status": status.get("overallStatus"),
        "conditions": conds.get("conditions", []),
        "eligibility": elig.get("eligibilityCriteria"),
        "locations": cities,
        "url": f"https://clinicaltrials.gov/study/{ident.get('nctId')}",
    }


def fetch_glioma_trials(page_size: int = 20) -> list[dict[str, Any]]:
    """Pull recruiting glioma trials, newest-relevant first, flattened."""
    params = {
        "query.cond": "glioma",
        "filter.overallStatus": "RECRUITING",
        "pageSize": page_size,
        "fields": ",".join(_FIELDS),
    }
    resp = requests.get(CTGOV_URL, params=params, timeout=30)
    resp.raise_for_status()
    studies = resp.json().get("studies", [])
    return [_flatten(s) for s in studies]
