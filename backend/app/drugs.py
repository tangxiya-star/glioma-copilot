"""Drug-name normalization — RxNorm (Tier 1) + ChEMBL (Tier 2), key-free.

Claude extracts a messy drug MENTION from the report ("Temodar", "TMZ", "bevacizumab");
this module resolves it to an AUTHORITATIVE identity, so drug identity is grounded in a
public source rather than the model — reinforcing "Claude is not the source of truth."

  Tier 1 — RxNorm via the RxNav REST API:
    mention -> RxCUI -> canonical INGREDIENT (brand/synonym/abbrev collapse to one drug).
  Tier 2 — ChEMBL REST API:
    ingredient -> ChEMBL molecule -> MECHANISM OF ACTION / drug class
    (e.g. bevacizumab -> "Vascular endothelial growth factor A inhibitor") — this is
    what lets "prior anti-VEGF therapy"-type eligibility match a specific drug.

Results are cached in Postgres (and in-process) — external lookups are done once.
"""

from typing import Any

import requests

RXNAV = "https://rxnav.nlm.nih.gov/REST"
CHEMBL = "https://www.ebi.ac.uk/chembl/api/data"

_MEM_CACHE: dict[str, dict] = {}


def _get_json(url: str, params: dict | None = None, timeout: int = 15) -> dict:
    resp = requests.get(url, params=params, timeout=timeout,
                        headers={"Accept": "application/json"})
    resp.raise_for_status()
    return resp.json()


# --- Tier 1: RxNorm (RxNav) ---------------------------------------------------

def _rxnorm_rxcui(name: str) -> tuple[str | None, str | None]:
    """Resolve a drug mention to (rxcui, matched_name) via exact then approximate match."""
    try:
        d = _get_json(f"{RXNAV}/rxcui.json", {"name": name, "search": 1})
        ids = (d.get("idGroup") or {}).get("rxnormId") or []
        if ids:
            return ids[0], name
    except Exception:
        pass
    # Fallback: approximate match handles brand names / abbreviations / typos.
    try:
        d = _get_json(f"{RXNAV}/approximateTerm.json", {"term": name, "maxEntries": 1})
        cands = (d.get("approximateGroup") or {}).get("candidate") or []
        for c in cands:
            if c.get("rxcui"):
                return c["rxcui"], c.get("name")
    except Exception:
        pass
    return None, None


def _rxnorm_ingredient(rxcui: str) -> tuple[str | None, str | None]:
    """Map an RxCUI to its canonical ingredient (rxcui, name). Falls back to self."""
    try:
        d = _get_json(f"{RXNAV}/rxcui/{rxcui}/related.json", {"tty": "IN"})
        for grp in (d.get("relatedGroup") or {}).get("conceptGroup") or []:
            for cp in grp.get("conceptProperties") or []:
                if cp.get("name"):
                    return cp.get("rxcui"), cp.get("name")
    except Exception:
        pass
    return None, None


# --- Tier 2: ChEMBL (mechanism / drug class) ----------------------------------

def _chembl_molecule(name: str) -> tuple[str | None, str | None]:
    try:
        d = _get_json(f"{CHEMBL}/molecule/search.json", {"q": name, "limit": 1})
        mols = d.get("molecules") or []
        if mols:
            return mols[0].get("molecule_chembl_id"), mols[0].get("pref_name")
    except Exception:
        pass
    return None, None


def _chembl_mechanisms(chembl_id: str) -> list[dict]:
    try:
        d = _get_json(f"{CHEMBL}/mechanism.json", {"molecule_chembl_id": chembl_id})
        return [
            {"mechanism_of_action": m.get("mechanism_of_action"),
             "action_type": m.get("action_type")}
            for m in (d.get("mechanisms") or [])
            if m.get("mechanism_of_action")
        ]
    except Exception:
        return []


# --- Public API ---------------------------------------------------------------

def normalize_drug(name: str) -> dict[str, Any]:
    """Normalize one drug mention -> authoritative RxNorm + ChEMBL identity."""
    key = (name or "").strip().lower()
    if not key:
        return {"input": name, "rxcui": None, "ingredient": None,
                "chembl_id": None, "mechanisms": [], "sources": {}}
    if key in _MEM_CACHE:
        return _MEM_CACHE[key]

    rxcui, matched = _rxnorm_rxcui(name)
    ing_cui, ingredient = _rxnorm_ingredient(rxcui) if rxcui else (None, None)
    canonical = ingredient or matched or name

    chembl_id, chembl_name = _chembl_molecule(canonical)
    mechanisms = _chembl_mechanisms(chembl_id) if chembl_id else []

    result = {
        "input": name,
        "rxcui": ing_cui or rxcui,
        "ingredient": canonical,
        "chembl_id": chembl_id,
        "chembl_name": chembl_name,
        "mechanisms": mechanisms,
        "sources": {
            "rxnorm": f"https://mor.nlm.nih.gov/RxNav/search?searchBy=RXCUI&searchTerm={ing_cui or rxcui}" if (ing_cui or rxcui) else None,
            "chembl": f"https://www.ebi.ac.uk/chembl/explore/compound/{chembl_id}" if chembl_id else None,
        },
    }
    _MEM_CACHE[key] = result
    return result
