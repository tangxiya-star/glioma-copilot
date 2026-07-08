"""Demo patients — REAL de-identified molecular data + a labeled constructed layer.

Honesty design (see CLAUDE.md + memory `glioma-demo-honesty`):
  * The MOLECULAR profile and basic demographics of each case are REAL, pulled
    from a public, de-identified TCGA sample via cBioPortal — study
    `lgggbm_tcga_pub` (Ceccarelli et al., *Cell* 2016, PMID 26824661; the
    "Merged Cohort of LGG and GBM", 1,122 tumors). TCGA is de-identified at
    source (barcodes, no names). Each case shows its sample id + a clickable
    cBioPortal link so a reviewer can trace every marker to the source.
  * The CLINICAL NARRATIVE (disease course, prior treatment such as
    bevacizumab, recurrence), the microscopic description, the IHC reagent/clone
    lines, and the "EGFR not yet tested" gate in Case 001 are a CONSTRUCTED /
    ILLUSTRATIVE demo layer — no public API carries them. They are labeled as
    such in every report and are NOT presented as real per-sample findings.
    (IHC clones named are genuine, widely-used reagents, cited as illustrative
    of a standard neuropathology workup — not a claim about the TCGA run.)
  * Patient PREFERENCES are deliberately NOT in these charts (a real chart never
    says "prefers not to travel"). They belong in the Day-5 shared-decision
    form, entered by the patient (doctor-guided).

The reports are formatted like a real integrated neuropathology & molecular
diagnostic report so the demo reads as clinician software. The report box stays
editable, so a reviewer can paste any report live.
"""

_STUDY = "lgggbm_tcga_pub"
_STUDY_NAME = "Merged Cohort of LGG and GBM — TCGA, Cell 2016 (Ceccarelli et al.)"
_PMID = "26824661"
# Obviously-fake sign-out so the demo chart looks complete without impersonating
# a real pathologist.
_SIGN_OUT = "[demo signature] Neuropathology service — synthetic sign-out, not a real physician"


def _cbio_url(sample_id: str) -> str:
    # Patient/sample barcodes are the TCGA case id (drop the "-01" sample suffix).
    case_id = sample_id.rsplit("-", 1)[0]
    return f"https://www.cbioportal.org/patient?studyId={_STUDY}&caseId={case_id}"


def _provenance(sample_id: str, markers: dict) -> dict:
    return {
        "sample_id": sample_id,
        "study": _STUDY,
        "study_name": _STUDY_NAME,
        "pmid": _PMID,
        "url": _cbio_url(sample_id),
        "markers": markers,  # the REAL curated fields, verbatim from cBioPortal
    }


def _report(prov: dict, *, specimen: str, clinical_history: str,
            microscopic: str, ihc: str, molecular: str, integrated_dx: str) -> str:
    """Assemble one integrated neuropathology report from real + constructed parts."""
    m = prov["markers"]
    return f"""INTEGRATED NEUROPATHOLOGY & MOLECULAR DIAGNOSTIC REPORT
(demo chart — REAL molecular data + a clearly labeled CONSTRUCTED clinical layer)

MOLECULAR SOURCE (REAL, de-identified): {prov['sample_id']} · cBioPortal study
{prov['study']} (TCGA, Cell 2016; PMID {prov['pmid']}).
{prov['url']}

PATIENT / SPECIMEN
- Patient: {m['AGE']}-year-old {m['SEX'].lower()} (age & sex from the TCGA sample).
- Specimen: {specimen}

CLINICAL HISTORY  [CONSTRUCTED — illustrative, not from TCGA]
{clinical_history}

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


# --- Case 001: real GBM IDH-wildtype (TCGA-02-0033) ---------------------------
# Real curated fields: 54yo Male, glioblastoma, WHO G4, IDH WT, IDHwt subtype,
# MGMT Methylated, ATRX WT (retained). Real mutation call: TP53 R248Q.
# Constructed layer: recurrence, prior Stupp, EGFR "pending" (the verify-catch gate).
_PROV_001 = _provenance("TCGA-02-0033-01", {
    "IDH_STATUS": "WT", "IDH_CODEL_SUBTYPE": "IDHwt",
    "MGMT_PROMOTER_STATUS": "Methylated", "ATRX_STATUS": "WT (retained)",
    "GRADE": "G4", "HISTOLOGICAL_DIAGNOSIS": "glioblastoma",
    "AGE": "54", "SEX": "Male", "mutations": "TP53 R248Q",
})
CASE_001 = {
    "id": "case-001",
    "label": "Case 001 — 54yo M, glioblastoma IDH-wildtype (TCGA-02-0033)",
    "provenance": _PROV_001,
    "clinical": {"recurrent": True, "prior_bevacizumab": False},
    "report": _report(
        _PROV_001,
        specimen="Right frontal brain tumor, craniotomy with resection.",
        clinical_history=(
            "- Right frontal glioblastoma; initial maximal safe resection.\n"
            "- First-line chemoradiation with concurrent + adjuvant TEMOZOLOMIDE (Stupp).\n"
            "- Now at FIRST RECURRENCE: measurable enhancing disease on MRI (RANO);\n"
            "  no therapy yet for this recurrence. No prior bevacizumab.\n"
            "- Performance status ECOG 1 (KPS ~80). Location: California."
        ),
        microscopic=(
            "Diffuse astrocytic glioma with brisk mitotic activity, MICROVASCULAR\n"
            "PROLIFERATION and NECROSIS."
        ),
        ihc=(
            "    - IDH1 R132H (clone H09): NEGATIVE.\n"
            "    - ATRX (clone CL0537): retained (intact nuclear expression).\n"
            "    - p53 (clone DO-7): scattered positivity, consistent with TP53 mutation.\n"
            "    - Ki-67 (clone MIB-1): proliferation index ~25%.\n"
            "    - H3 K27M (clone RM192): not detected."
        ),
        molecular=(
            "    - IDH1/2 (whole-exome sequencing): WILD-TYPE (no R132 mutation).\n"
            "    - 1p/19q (copy-number array): non-codeleted.\n"
            "    - MGMT promoter (methylation array): METHYLATED.\n"
            "    - TP53 (WES): mutated — R248Q.\n"
            "    - EGFR: NOT YET TESTED — amplification / EGFRvIII status UNKNOWN\n"
            "      (pending).  [CONSTRUCTED gate — illustrative, not from TCGA]"
        ),
        integrated_dx="Glioblastoma, IDH-wildtype, CNS WHO grade 4 — recurrent.",
    ),
}

# --- Case 002: real IDH-mutant astrocytoma, grade 4 (TCGA-02-2483) -----------
# Real: 43yo Male, IDH Mutant, non-codel, G4, ATRX Mutant (lost), MGMT Methylated,
# TERT WT. Real variant calls: IDH1 R132H, ATRX W2001Cfs*14 (truncating), TP53 R273H.
_PROV_002 = _provenance("TCGA-02-2483-01", {
    "IDH_STATUS": "Mutant", "IDH_CODEL_SUBTYPE": "IDHmut-non-codel",
    "MGMT_PROMOTER_STATUS": "Methylated", "TERT_PROMOTER_STATUS": "WT",
    "ATRX_STATUS": "Mutant (loss)", "GRADE": "G4",
    "HISTOLOGICAL_DIAGNOSIS": "glioblastoma (IDH-mutant → astrocytoma grade 4 under WHO CNS5)",
    "AGE": "43", "SEX": "Male",
    "mutations": "IDH1 R132H, ATRX W2001Cfs*14, TP53 R273H",
})
CASE_002 = {
    "id": "case-002",
    "label": "Case 002 — 43yo M, astrocytoma IDH-mutant grade 4 (TCGA-02-2483)",
    "provenance": _PROV_002,
    "clinical": {"recurrent": False, "prior_bevacizumab": False},
    "report": _report(
        _PROV_002,
        specimen="Left temporal brain tumor, craniotomy with resection.",
        clinical_history=(
            "- Newly diagnosed left temporal diffuse glioma; maximal safe resection.\n"
            "- No prior chemotherapy or radiation. No prior bevacizumab.\n"
            "- Performance status ECOG 0. Location: New York."
        ),
        microscopic=(
            "Diffuse astrocytoma with increased cellularity and mitotic activity;\n"
            "microvascular proliferation and necrosis present (grade-4 features)."
        ),
        ihc=(
            "    - IDH1 R132H (clone H09): POSITIVE (strong cytoplasmic).\n"
            "    - ATRX (clone CL0537): LOSS of nuclear expression.\n"
            "    - p53 (clone DO-7): strong diffuse positivity, consistent with TP53 mutation.\n"
            "    - Ki-67 (clone MIB-1): proliferation index elevated.\n"
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

# --- Case 003: real oligodendroglioma, IDH-mut & 1p/19q-codeleted (TCGA-CS-5396)
# Real: 53yo Female, oligodendroglioma, G3, IDH Mutant, codel, TERT Mutant,
# ATRX WT (retained), MGMT Methylated. Real variant calls: IDH1 R132H, TP53 R273H.
_PROV_003 = _provenance("TCGA-CS-5396-01", {
    "IDH_STATUS": "Mutant", "IDH_CODEL_SUBTYPE": "IDHmut-codel",
    "MGMT_PROMOTER_STATUS": "Methylated", "TERT_PROMOTER_STATUS": "Mutant",
    "ATRX_STATUS": "WT (retained)", "GRADE": "G3",
    "HISTOLOGICAL_DIAGNOSIS": "oligodendroglioma",
    "AGE": "53", "SEX": "Female", "mutations": "IDH1 R132H, TP53 R273H",
})
CASE_003 = {
    "id": "case-003",
    "label": "Case 003 — 53yo F, oligodendroglioma IDH-mut 1p/19q-codel (TCGA-CS-5396)",
    "provenance": _PROV_003,
    "clinical": {"recurrent": False, "prior_bevacizumab": False},
    "report": _report(
        _PROV_003,
        specimen="Right frontal brain tumor, craniotomy with resection.",
        clinical_history=(
            "- Right frontal diffuse glioma; gross-total resection.\n"
            "- No prior chemotherapy or radiation. No prior bevacizumab.\n"
            "- Performance status ECOG 0. Location: Illinois."
        ),
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

# --- Case 004: real GBM IDH-wildtype (TCGA-02-0003), prior-bevacizumab demo ---
# Real: 50yo Male, glioblastoma, G4, IDH WT, MGMT Unmethylated, ATRX WT.
# Real variant calls: EGFR C620Y, TP53 H178Q, TP53 R282W.
# Constructed layer: recurrence + prior bevacizumab (the buried-exclusion demo).
_PROV_004 = _provenance("TCGA-02-0003-01", {
    "IDH_STATUS": "WT", "IDH_CODEL_SUBTYPE": "IDHwt",
    "MGMT_PROMOTER_STATUS": "Unmethylated", "ATRX_STATUS": "WT (retained)",
    "GRADE": "G4", "HISTOLOGICAL_DIAGNOSIS": "glioblastoma",
    "AGE": "50", "SEX": "Male", "mutations": "EGFR C620Y, TP53 H178Q, TP53 R282W",
})
CASE_004 = {
    "id": "case-004",
    "label": "Case 004 — 50yo M, recurrent glioblastoma IDH-wt · prior bevacizumab (TCGA-02-0003)",
    "provenance": _PROV_004,
    "clinical": {"recurrent": True, "prior_bevacizumab": True},
    "report": _report(
        _PROV_004,
        specimen="Left parietal brain tumor, craniotomy with resection.",
        clinical_history=(
            "- Left parietal glioblastoma; initial subtotal resection.\n"
            "- First-line chemoradiation with concurrent + adjuvant TEMOZOLOMIDE (Stupp).\n"
            "- At progression started BEVACIZUMAB (several cycles); now further progression\n"
            "  ON bevacizumab, seeking a clinical trial.\n"
            "- Performance status ECOG 1 (KPS ~80). Location: California."
        ),
        microscopic=(
            "Diffuse astrocytic glioma with brisk mitotic activity, MICROVASCULAR\n"
            "PROLIFERATION and NECROSIS."
        ),
        ihc=(
            "    - IDH1 R132H (clone H09): NEGATIVE.\n"
            "    - ATRX (clone CL0537): retained.\n"
            "    - p53 (clone DO-7): positivity consistent with TP53 mutation.\n"
            "    - Ki-67 (clone MIB-1): proliferation index ~30%.\n"
            "    - H3 K27M (clone RM192): not detected."
        ),
        molecular=(
            "    - IDH1/2 (whole-exome sequencing): WILD-TYPE (no R132 mutation).\n"
            "    - 1p/19q (copy-number array): non-codeleted.\n"
            "    - MGMT promoter (methylation array): UNMETHYLATED.\n"
            "    - EGFR (WES): mutated — C620Y (tested).\n"
            "    - TP53 (WES): mutated — H178Q, R282W."
        ),
        integrated_dx="Glioblastoma, IDH-wildtype, CNS WHO grade 4 — recurrent.",
    ),
}

SYNTHETIC_PATIENTS = [CASE_001, CASE_002, CASE_003, CASE_004]

# Default patient (used where a single case is needed, e.g. extract/classify defaults).
SYNTHETIC_PATIENT = CASE_001

_BY_ID = {p["id"]: p for p in SYNTHETIC_PATIENTS}


def get_patient(patient_id: str | None):
    """Return a patient by id, or the default case if id is missing/unknown."""
    if patient_id and patient_id in _BY_ID:
        return _BY_ID[patient_id]
    return SYNTHETIC_PATIENT
