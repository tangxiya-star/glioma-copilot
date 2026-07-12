"""Demo patients — REAL de-identified data from LIVING TCGA patients + a tiny labeled overlay.

Honesty design (see CLAUDE.md + memory `glioma-demo-honesty`):
  * MOLECULAR profile + demographics are REAL, from a public de-identified TCGA sample
    via cBioPortal — study `lgggbm_tcga_pub` (Ceccarelli et al., *Cell* 2016,
    PMID 26824661). Each case links to its exact sample on cBioPortal.
  * PRIOR TREATMENT is REAL too, from the NIH **GDC** (Genomic Data Commons) clinical
    files for the same TCGA case (treatment_type + therapeutic_agents). Each case links
    to its GDC case record. So temozolomide / radiation / bevacizumab are actual recorded
    therapies for that patient — not invented.
  * All four cases are patients recorded as **ALIVE** in TCGA. We deliberately do NOT
    surface vital status / survival anywhere (red line: no individual survival prognosis,
    and out of respect — these are real people).
  * The ONLY constructed bit is a small, clearly-labeled overlay: Case 001's "EGFR not
    yet tested" gate (the open question the verify-catch demo turns on) and a light
    "under review at recurrence/progression" framing. No molecular or treatment fact is
    invented.
  * Patient PREFERENCES are NOT in the chart — they belong in the Day-5 shared-decision
    form (doctor-guided).
"""

_STUDY = "lgggbm_tcga_pub"
_STUDY_NAME = "Merged Cohort of LGG and GBM — TCGA, Cell 2016 (Ceccarelli et al.)"
_PMID = "26824661"
_SIGN_OUT = "[demo signature] Neuropathology service — synthetic sign-out, not a real physician"


def _cbio_url(sample_id: str) -> str:
    case_id = sample_id.rsplit("-", 1)[0]
    return f"https://www.cbioportal.org/patient?studyId={_STUDY}&caseId={case_id}"


def _gdc_url(uuid: str) -> str:
    return f"https://portal.gdc.cancer.gov/cases/{uuid}"


def _provenance(sample_id: str, gdc_uuid: str, agents: list[str], markers: dict,
                clinical: dict | None = None) -> dict:
    return {
        "sample_id": sample_id,
        "study": _STUDY,
        "study_name": _STUDY_NAME,
        "pmid": _PMID,
        "url": _cbio_url(sample_id),
        "markers": markers,  # REAL curated cBioPortal fields
        "treatment": {        # REAL GDC treatment record
            "source": "NIH GDC (portal.gdc.cancer.gov) — TCGA clinical",
            "url": _gdc_url(gdc_uuid),
            "agents": agents,
        },
        "clinical": clinical or {},  # REAL clinical: KPS, tumor site, primary dx
    }


_CLIN_LABELS = {
    "status": "Disease status", "resection": "Resection extent",
    "steroid": "Steroid", "location": "Tumor location", "measurable": "Measurable disease",
}


def _report(prov: dict, *, specimen: str, prior_therapy: str, overlay: str,
            microscopic: str, ihc: str, molecular: str, integrated_dx: str) -> str:
    m = prov["markers"]
    cl = prov.get("clinical", {})
    _constructed = cl.get("_constructed", [])
    constructed_clin = "\n".join(
        f"- {_CLIN_LABELS.get(k, k)}: {cl[k]}" for k in _constructed if cl.get(k)
    )
    constructed_block = (
        f"\nCONSTRUCTED CLINICAL LAYER  [illustrative — NOT from TCGA]\n{constructed_clin}\n"
        if constructed_clin else ""
    )

    # A field that is authored (in _constructed) must NOT appear under the REAL header —
    # it is rendered in the constructed_block instead. Skipping it here keeps the report
    # internally consistent (e.g. disease status shown once, as constructed, not also as
    # a contradicting "Newly diagnosed" line from GDC).
    def _real_line(key, label):
        return "" if key in _constructed else f"- {label}: {cl.get(key, '—')}\n"
    clinical_real = (
        f"- Primary diagnosis: {cl.get('primary_diagnosis', '—')}\n"
        + _real_line("status", "Disease status")
        + _real_line("resection", "Resection")
        + f"- Tumor site: {cl.get('site', '—')}\n"
        + f"- Performance status: KPS {cl.get('performance_kps', '—')}"
    )
    return f"""INTEGRATED NEUROPATHOLOGY & MOLECULAR DIAGNOSTIC REPORT
(demo chart — REAL molecular + REAL treatment data; a small labeled overlay is marked)

MOLECULAR SOURCE (REAL, de-identified): {prov['sample_id']} · cBioPortal study
{prov['study']} (TCGA, Cell 2016; PMID {prov['pmid']}).
{prov['url']}
TREATMENT SOURCE (REAL, de-identified): NIH GDC — same TCGA case.
{prov['treatment']['url']}

PATIENT / SPECIMEN
- Patient: {m['AGE']}-year-old {m['SEX'].lower()} (age & sex from the TCGA sample).
- Specimen: {specimen}

CLINICAL  [REAL — cBioPortal + GDC]
{clinical_real}
{constructed_block}
PRIOR THERAPY  [REAL — GDC treatment record for this patient]
{prior_therapy}
{overlay}
MICROSCOPIC DESCRIPTION  [illustrative of the TCGA grade / histology label]
{microscopic}

ANCILLARY STUDIES
  Immunohistochemistry [illustrative reagents / clones — standard workup]:
{ihc}
  Molecular / genomic [REAL — TCGA whole-exome + array calls for this sample]:
{molecular}

INTEGRATED DIAGNOSIS (WHO CNS5, 2021)
{integrated_dx}

Electronically signed: {_SIGN_OUT}
"""


# --- Case 001: real GBM IDH-wildtype, LIVING (TCGA-06-6695) -------------------
# Real: 64yo M, glioblastoma, G4, IDH WT, MGMT methylated, ATRX WT. GDC tx: TMZ + RT.
# Overlay: "EGFR not yet tested" gate (the verify-catch scenario).
_PROV_001 = _provenance(
    "TCGA-06-6695-01", "0628cb4a-c480-4b2f-bd2e-bb33e6994302",
    ["temozolomide", "radiation (external beam)"],
    {"IDH_STATUS": "WT", "IDH_CODEL_SUBTYPE": "IDHwt",
     "MGMT_PROMOTER_STATUS": "Methylated", "ATRX_STATUS": "WT (retained)",
     "GRADE": "G4", "HISTOLOGICAL_DIAGNOSIS": "glioblastoma",
     "AGE": "64", "SEX": "Male",
     "mutations": "none reported in IDH1/ATRX/TERT/EGFR/TP53 panel"},
    clinical={"primary_diagnosis": "Glioblastoma", "site": "Brain, NOS", "performance_kps": "40",
              "status": "First recurrence (illustrative clinical course)", "resection": "Surgical resection",
              "steroid": "Dexamethasone 4 mg/day", "location": "Right frontal, supratentorial",
              "_constructed": ["status", "steroid", "location"]})
CASE_001 = {
    "id": "case-001",
    "label": "Case 001 — 64yo M, glioblastoma IDH-wildtype (TCGA-06-6695)",
    "provenance": _PROV_001,
    "clinical": {"recurrent": True, "prior_bevacizumab": False},
    "report": _report(
        _PROV_001,
        specimen="Brain tumor, craniotomy with resection.",
        prior_therapy=(
            "- RADIATION (external beam) + TEMOZOLOMIDE (first-line chemoradiation)\n"
            "  — recorded in the GDC treatment file for this patient."
        ),
        overlay=(
            "\nOVERLAY  [CONSTRUCTED, illustrative — not from TCGA]\n"
            "- Presented for review at recurrence; no therapy yet for this recurrence.\n"
            "- EGFR amplification / EGFRvIII: NOT YET TESTED (pending) — the open question\n"
            "  this review turns on.\n"
        ),
        microscopic=(
            "Diffuse astrocytic glioma with brisk mitotic activity, MICROVASCULAR\n"
            "PROLIFERATION and NECROSIS."
        ),
        ihc=(
            "    - IDH1 R132H (clone H09): NEGATIVE.\n"
            "    - ATRX (clone CL0537): retained.\n"
            "    - Ki-67 (clone MIB-1): elevated proliferation index.\n"
            "    - H3 K27M (clone RM192): not detected."
        ),
        molecular=(
            "    - IDH1/2 (whole-exome sequencing): WILD-TYPE (no R132 mutation).\n"
            "    - 1p/19q (copy-number array): non-codeleted.\n"
            "    - MGMT promoter (methylation array): METHYLATED.\n"
            "    - ATRX: retained.\n"
            "    - EGFR: NOT YET TESTED — amplification / EGFRvIII UNKNOWN (pending).\n"
            "      [OVERLAY — illustrative gate, not from TCGA]"
        ),
        integrated_dx="Glioblastoma, IDH-wildtype, CNS WHO grade 4 — recurrent.",
    ),
}

# --- Case 002: real IDH-mutant astrocytoma, grade 4, LIVING (TCGA-02-2483) ----
_PROV_002 = _provenance(
    "TCGA-02-2483-01", "a2ac9937-f351-4d78-9261-264bf6c21e0c",
    ["temozolomide", "radiation (external beam)"],
    {"IDH_STATUS": "Mutant", "IDH_CODEL_SUBTYPE": "IDHmut-non-codel",
     "MGMT_PROMOTER_STATUS": "Methylated", "TERT_PROMOTER_STATUS": "WT",
     "ATRX_STATUS": "Mutant (loss)", "GRADE": "G4",
     "HISTOLOGICAL_DIAGNOSIS": "glioblastoma (IDH-mutant → astrocytoma grade 4 under WHO CNS5)",
     "AGE": "43", "SEX": "Male",
     "mutations": "IDH1 R132H, ATRX W2001Cfs*14, TP53 R273H"},
    clinical={"primary_diagnosis": "Glioblastoma", "site": "Brain, NOS", "performance_kps": "80",
              "status": "Newly diagnosed", "resection": "Biopsy",
              "steroid": "None", "location": "Left temporal, supratentorial",
              "_constructed": ["steroid", "location"]})
CASE_002 = {
    "id": "case-002",
    "label": "Case 002 — 43yo M, astrocytoma IDH-mutant grade 4 (TCGA-02-2483)",
    "provenance": _PROV_002,
    "clinical": {"recurrent": False, "prior_bevacizumab": False},
    "report": _report(
        _PROV_002,
        specimen="Brain tumor, craniotomy with resection.",
        prior_therapy=(
            "- RADIATION (external beam) + TEMOZOLOMIDE (adjuvant chemoradiation)\n"
            "  — recorded in the GDC treatment file for this patient."
        ),
        overlay="",
        microscopic=(
            "Diffuse astrocytoma with increased cellularity and mitotic activity;\n"
            "microvascular proliferation and necrosis present (grade-4 features)."
        ),
        ihc=(
            "    - IDH1 R132H (clone H09): POSITIVE (strong cytoplasmic).\n"
            "    - ATRX (clone CL0537): LOSS of nuclear expression.\n"
            "    - p53 (clone DO-7): strong diffuse positivity, consistent with TP53 mutation.\n"
            "    - Ki-67 (clone MIB-1): elevated proliferation index.\n"
            "    - H3 K27M (clone RM192): not detected."
        ),
        molecular=(
            "    - IDH1 (whole-exome sequencing): MUTANT — R132H.\n"
            "    - 1p/19q (copy-number array): non-codeleted.\n"
            "    - ATRX (WES): truncating — W2001Cfs*14 (loss).\n"
            "    - TP53 (WES): mutated — R273H.\n"
            "    - TERT promoter: wild-type.\n"
            "    - MGMT promoter (methylation array): METHYLATED."
        ),
        integrated_dx=(
            "Astrocytoma, IDH-mutant, CNS WHO grade 4 (IDH-mutant, 1p/19q non-codeleted,\n"
            "ATRX-lost; grade 4 by high-grade histologic features)."
        ),
    ),
}

# --- Case 003: real oligodendroglioma, LIVING (TCGA-CS-5396) ------------------
_PROV_003 = _provenance(
    "TCGA-CS-5396-01", "b6c2c9bd-625b-4a98-830c-49c344f6cb5f",
    ["temozolomide", "radiation (external beam)"],
    {"IDH_STATUS": "Mutant", "IDH_CODEL_SUBTYPE": "IDHmut-codel",
     "MGMT_PROMOTER_STATUS": "Methylated", "TERT_PROMOTER_STATUS": "Mutant",
     "ATRX_STATUS": "WT (retained)", "GRADE": "G3",
     "HISTOLOGICAL_DIAGNOSIS": "oligodendroglioma",
     "AGE": "53", "SEX": "Female", "mutations": "IDH1 R132H, TP53 R273H"},
    clinical={"primary_diagnosis": "Oligodendroglioma, anaplastic", "site": "Nervous system, NOS",
              "performance_kps": "90", "status": "Newly diagnosed",
              "steroid": "None", "location": "Right frontal, supratentorial",
              "_constructed": ["steroid", "location"]})
CASE_003 = {
    "id": "case-003",
    "label": "Case 003 — 53yo F, oligodendroglioma IDH-mut 1p/19q-codel (TCGA-CS-5396)",
    "provenance": _PROV_003,
    "clinical": {"recurrent": False, "prior_bevacizumab": False},
    "report": _report(
        _PROV_003,
        specimen="Brain tumor, craniotomy with resection.",
        prior_therapy=(
            "- RADIATION (external beam) + TEMOZOLOMIDE (adjuvant chemoradiation)\n"
            "  — recorded in the GDC treatment file for this patient."
        ),
        overlay="",
        microscopic=(
            "Diffuse glioma with monomorphic rounded nuclei and perinuclear halos\n"
            "('fried-egg' artifact) and a delicate branching ('chicken-wire') capillary\n"
            "network. Low mitotic activity; no microvascular proliferation or necrosis."
        ),
        ihc=(
            "    - IDH1 R132H (clone H09): POSITIVE.\n"
            "    - ATRX (clone CL0537): retained (intact) — supports oligodendroglioma.\n"
            "    - Ki-67 (clone MIB-1): low-to-moderate proliferation index.\n"
            "    - H3 K27M (clone RM192): not detected."
        ),
        molecular=(
            "    - IDH1 (whole-exome sequencing): MUTANT — R132H.\n"
            "    - 1p/19q (copy-number array): CO-DELETED (whole-arm loss of 1p and 19q).\n"
            "    - TERT promoter: MUTATED.\n"
            "    - ATRX (WES): retained.\n"
            "    - TP53 (WES): R273H.\n"
            "    - MGMT promoter (methylation array): METHYLATED."
        ),
        integrated_dx=(
            "Oligodendroglioma, IDH-mutant and 1p/19q-codeleted, CNS WHO grade 3."
        ),
    ),
}

# --- Case 004: real GBM IDH-wildtype, LIVING, REAL prior bevacizumab (TCGA-06-5413)
# Real: 67yo M, glioblastoma, G4, IDH WT, MGMT unmethylated, ATRX WT.
# GDC tx: TMZ + radiation + BEVACIZUMAB (real anti-VEGF record) — the exclusion demo.
_PROV_004 = _provenance(
    "TCGA-06-5413-01", "8d2e88d9-d8d0-4c42-8aa2-205a788dea58",
    ["temozolomide", "bevacizumab", "radiation (external beam)"],
    {"IDH_STATUS": "WT", "IDH_CODEL_SUBTYPE": "IDHwt",
     "MGMT_PROMOTER_STATUS": "Unmethylated", "ATRX_STATUS": "WT (retained)",
     "GRADE": "G4", "HISTOLOGICAL_DIAGNOSIS": "glioblastoma",
     "AGE": "67", "SEX": "Male",
     "mutations": "none reported in IDH1/ATRX/TERT/EGFR/TP53 panel"},
    clinical={"primary_diagnosis": "Glioblastoma", "site": "Brain, NOS", "performance_kps": "60",
              "status": "First recurrence (illustrative clinical course)", "resection": "Surgical resection",
              "steroid": "Dexamethasone 2 mg/day", "location": "Left parietal, supratentorial",
              "_constructed": ["status", "steroid", "location"]})
CASE_004 = {
    "id": "case-004",
    "label": "Case 004 — 67yo M, glioblastoma IDH-wt · prior bevacizumab (TCGA-06-5413)",
    "provenance": _PROV_004,
    "clinical": {"recurrent": True, "prior_bevacizumab": True},
    "report": _report(
        _PROV_004,
        specimen="Brain tumor, craniotomy with resection.",
        prior_therapy=(
            "- RADIATION (external beam) + TEMOZOLOMIDE (first-line chemoradiation),\n"
            "  then BEVACIZUMAB (anti-VEGF) — ALL recorded in the GDC treatment file for\n"
            "  this patient. (Bevacizumab is a common later-line / recurrence agent in GBM.)"
        ),
        overlay=(
            "\nOVERLAY  [CONSTRUCTED, illustrative — not from TCGA]\n"
            "- Under review at progression for a next-line clinical trial.\n"
        ),
        microscopic=(
            "Diffuse astrocytic glioma with brisk mitotic activity, MICROVASCULAR\n"
            "PROLIFERATION and NECROSIS."
        ),
        ihc=(
            "    - IDH1 R132H (clone H09): NEGATIVE.\n"
            "    - ATRX (clone CL0537): retained.\n"
            "    - Ki-67 (clone MIB-1): elevated proliferation index.\n"
            "    - H3 K27M (clone RM192): not detected."
        ),
        molecular=(
            "    - IDH1/2 (whole-exome sequencing): WILD-TYPE (no R132 mutation).\n"
            "    - 1p/19q (copy-number array): non-codeleted.\n"
            "    - MGMT promoter (methylation array): UNMETHYLATED.\n"
            "    - ATRX: retained."
        ),
        integrated_dx="Glioblastoma, IDH-wildtype, CNS WHO grade 4 — recurrent.",
    ),
}

SYNTHETIC_PATIENTS = [CASE_001, CASE_002, CASE_003, CASE_004]

# 4 more real LIVING TCGA patients — a SNAPSHOT built once from cBioPortal + GDC via
# tcga.build_case_from_tcga (panel_extra.json), so the panel loads instantly / stably
# with no runtime API dependency. Together with the 4 curated cases = an 8-patient panel.
import json as _json  # noqa: E402
from pathlib import Path as _Path  # noqa: E402

_extra = _Path(__file__).parent / "panel_extra.json"
if _extra.exists():
    try:
        SYNTHETIC_PATIENTS.extend(_json.loads(_extra.read_text()))
    except Exception as _e:  # pragma: no cover
        print(f"[patient] panel_extra load skipped: {_e}")

# Default patient (used where a single case is needed, e.g. extract/classify defaults).
SYNTHETIC_PATIENT = CASE_001

_BY_ID = {p["id"]: p for p in SYNTHETIC_PATIENTS}


def get_patient(patient_id: str | None):
    """Return a patient by id, or the default case if id is missing/unknown."""
    if patient_id and patient_id in _BY_ID:
        return _BY_ID[patient_id]
    return SYNTHETIC_PATIENT


def register_patient(case: dict) -> dict:
    """Register a live-loaded case in the in-memory store so downstream analysis
    (fit / triage / review / drugs) can look it up by id. Transient (per process)."""
    _BY_ID[case["id"]] = case
    return case
