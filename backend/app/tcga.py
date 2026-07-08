"""Live case loader — build a case on the spot from a real de-identified TCGA barcode.

Given a TCGA barcode (e.g. "TCGA-06-6700"), this fetches — LIVE, at request time —
the molecular profile + variant calls from cBioPortal and the prior treatment from the
NIH GDC, and assembles a case in our report format. This is how a reviewer can drop in
*any* real de-identified patient during a demo and watch the whole pipeline run in
real time — proving nothing is pre-canned.

We deliberately do NOT fetch or surface survival / vital status (red line: no individual
prognosis; and out of respect). Only molecular + treatment are used.
"""

from typing import Any

import requests

STUDY = "lgggbm_tcga_pub"
STUDY_NAME = "Merged Cohort of LGG and GBM — TCGA, Cell 2016 (Ceccarelli et al.)"
PMID = "26824661"
CBIO = "https://www.cbioportal.org/api"
GDC = "https://api.gdc.cancer.gov"

_MARKER_KEYS = [
    "IDH_STATUS", "IDH_CODEL_SUBTYPE", "MGMT_PROMOTER_STATUS",
    "TERT_PROMOTER_STATUS", "ATRX_STATUS", "GRADE",
]


def _get(url: str, **kw):
    r = requests.get(url, timeout=25, headers={"Accept": "application/json"}, **kw)
    r.raise_for_status()
    return r.json()


def _cbio_clinical(path: str) -> dict[str, str]:
    try:
        return {x["clinicalAttributeId"]: x["value"] for x in _get(f"{CBIO}{path}")}
    except Exception:
        return {}


def _cbio_mutations(sample_id: str) -> list[str]:
    body = {"sampleIds": [sample_id],
            "entrezGeneIds": [3417, 546, 7015, 1956, 7157, 1029]}  # IDH1 ATRX TERT EGFR TP53 CDKN2A
    try:
        r = requests.post(
            f"{CBIO}/molecular-profiles/{STUDY}_mutations/mutations/fetch?projection=DETAILED",
            json=body, timeout=25, headers={"Accept": "application/json"})
        r.raise_for_status()
        return [f"{m['gene']['hugoGeneSymbol']} {m.get('proteinChange', '?')}" for m in r.json()]
    except Exception:
        return []


def _gdc_case(case_id: str) -> dict[str, Any]:
    import json as _json
    filt = {"op": "in", "content": {"field": "cases.submitter_id", "value": [case_id]}}
    params = {"filters": _json.dumps(filt),
              "expand": "diagnoses,diagnoses.treatments", "fields": "case_id,submitter_id",
              "format": "json", "size": "1"}
    try:
        hits = _get(f"{GDC}/cases", params=params)["data"]["hits"]
        if not hits:
            return {"agents": [], "uuid": None}
        h = hits[0]
        agents = []
        dx = {}
        for dg in h.get("diagnoses", []):
            for t in dg.get("treatments", []) or []:
                if t.get("treatment_or_therapy") == "yes":
                    a = t.get("therapeutic_agents") or t.get("treatment_type")
                    if a:
                        agents.append(a.lower())
            if not dx:  # first diagnosis carries the clinical fields
                dx = {
                    "primary_diagnosis": dg.get("primary_diagnosis"),
                    "site": dg.get("site_of_resection_or_biopsy") or dg.get("tissue_or_organ_of_origin"),
                    "prior_malignancy": dg.get("prior_malignancy"),
                }
        return {"agents": sorted(set(agents)), "uuid": h.get("case_id"), **dx}
    except Exception:
        return {"agents": [], "uuid": None}


def _normalize_barcode(barcode: str) -> tuple[str, str]:
    """Return (sample_id, case_id) from a TCGA barcode with or without the sample suffix."""
    bc = barcode.strip().upper()
    parts = bc.split("-")
    if len(parts) <= 3:
        return f"{bc}-01", bc
    return bc, "-".join(parts[:3])


def build_case_from_tcga(barcode: str) -> dict[str, Any]:
    """Assemble a case dict {id,label,provenance,clinical,report} from a live TCGA barcode."""
    sample_id, case_id = _normalize_barcode(barcode)

    smpl = _cbio_clinical(f"/studies/{STUDY}/samples/{sample_id}/clinical-data?clinicalDataType=SAMPLE")
    if not smpl:
        raise ValueError(
            f"{sample_id} not found in cBioPortal {STUDY}. Use a de-identified TCGA "
            f"glioma barcode from that cohort, e.g. TCGA-06-6700."
        )
    pat = _cbio_clinical(f"/studies/{STUDY}/patients/{case_id}/clinical-data?clinicalDataType=PATIENT")

    markers = {k: smpl.get(k, "") for k in _MARKER_KEYS if smpl.get(k)}
    markers["AGE"] = (pat.get("AGE") or "").split(".")[0] or "unknown"
    markers["SEX"] = pat.get("SEX") or "unknown"
    markers["HISTOLOGICAL_DIAGNOSIS"] = pat.get("HISTOLOGICAL_DIAGNOSIS") or smpl.get("CANCER_TYPE_DETAILED", "glioma")
    muts = _cbio_mutations(sample_id)
    markers["mutations"] = ", ".join(muts) if muts else "none reported in IDH1/ATRX/TERT/EGFR/TP53 panel"

    gdc = _gdc_case(case_id)
    agents = gdc["agents"]
    prior_bev = any("bevacizumab" in a for a in agents)

    provenance = {
        "sample_id": sample_id,
        "study": STUDY,
        "study_name": STUDY_NAME,
        "pmid": PMID,
        "url": f"https://www.cbioportal.org/patient?studyId={STUDY}&caseId={case_id}",
        "markers": markers,
        "treatment": {
            "source": "NIH GDC (portal.gdc.cancer.gov) — TCGA clinical",
            "url": f"https://portal.gdc.cancer.gov/cases/{gdc['uuid']}" if gdc["uuid"] else "https://portal.gdc.cancer.gov/",
            "agents": agents or ["(no treatment recorded in GDC)"],
        },
    }

    idh = smpl.get("IDH_STATUS", "").lower()
    grade = smpl.get("GRADE", "")
    histo = markers["HISTOLOGICAL_DIAGNOSIS"].lower()
    high_grade = grade in ("G4", "G3") or "glioblastoma" in histo
    micro = (
        "Diffuse glioma with brisk mitotic activity, MICROVASCULAR PROLIFERATION and NECROSIS."
        if grade == "G4" or "glioblastoma" in histo
        else "Diffuse glioma; see molecular findings below."
    )

    def line(label, val):
        return f"    - {label}: {val}" if val else None

    mol = [
        line("IDH", "MUTANT" if idh == "mutant" else "WILD-TYPE" if idh == "wt" else smpl.get("IDH_STATUS")),
        line("1p/19q", smpl.get("IDH_CODEL_SUBTYPE")),
        line("MGMT promoter", smpl.get("MGMT_PROMOTER_STATUS")),
        line("TERT promoter", smpl.get("TERT_PROMOTER_STATUS")),
        line("ATRX", smpl.get("ATRX_STATUS")),
        line("Grade (TCGA)", grade),
        line("Variant calls", markers["mutations"]),
    ]
    mol_text = "\n".join(x for x in mol if x)
    tx_text = "\n".join(f"    - {a}" for a in agents) or "    - (no treatment recorded in GDC)"

    # Clinical (REAL): performance status from cBioPortal, site/primary dx from GDC.
    kps = pat.get("KARNOFSKY_PERFORMANCE_SCORE")
    clin = [
        f"- Primary diagnosis (GDC): {gdc.get('primary_diagnosis')}" if gdc.get("primary_diagnosis") else None,
        f"- Tumor site (GDC): {gdc.get('site')}" if gdc.get("site") else None,
        f"- Performance status: KPS {kps.split('.')[0]}" if kps else None,
        f"- Prior malignancy (GDC): {gdc.get('prior_malignancy')}" if gdc.get("prior_malignancy") else None,
    ]
    clin_text = "\n".join(x for x in clin if x) or "- (no additional clinical fields recorded)"

    report = f"""INTEGRATED NEUROPATHOLOGY & MOLECULAR DIAGNOSTIC REPORT — LIVE from TCGA
(fetched at request time; REAL de-identified data — molecular via cBioPortal, treatment via NIH GDC)

MOLECULAR SOURCE: {sample_id} · cBioPortal {STUDY} (TCGA, Cell 2016; PMID {PMID}).
{provenance['url']}
TREATMENT SOURCE: NIH GDC — same TCGA case. {provenance['treatment']['url']}

PATIENT / SPECIMEN
- Patient: {markers['AGE']}-year-old {markers['SEX'].lower()} (from the TCGA sample).
- Histologic diagnosis (TCGA): {histo}.

CLINICAL  [REAL — cBioPortal + GDC]
{clin_text}

PRIOR THERAPY  [REAL — GDC record]
{tx_text}

MICROSCOPIC DESCRIPTION  [illustrative of the TCGA grade / histology label]
{micro}

MOLECULAR / GENOMIC  [REAL — TCGA whole-exome + array calls]
{mol_text}
"""

    return {
        "id": f"live-{case_id}",
        "label": f"Live · {case_id} — {histo}{' G' + grade[-1] if grade.startswith('G') else ''} ({sample_id})",
        "provenance": provenance,
        "clinical": {"recurrent": False, "prior_bevacizumab": prior_bev},
        "report": report,
        # marker so the frontend/UI can tell this was loaded live
        "live": True,
    }
