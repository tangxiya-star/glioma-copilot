"""Demo patients — REAL de-identified molecular data + a labeled constructed layer.

Honesty design (see CLAUDE.md + memory `glioma-demo-honesty`):
  * The MOLECULAR profile and basic demographics of each case are REAL, pulled
    from a public, de-identified TCGA sample via cBioPortal — study
    `lgggbm_tcga_pub` (Ceccarelli et al., *Cell* 2016, PMID 26824661; the
    "Merged Cohort of LGG and GBM", 1,122 tumors). TCGA is de-identified at
    source (barcodes, no names). Each case shows its sample id + a clickable
    cBioPortal link so a reviewer can trace every marker to the source.
  * The CLINICAL NARRATIVE (disease course, prior treatment such as
    bevacizumab, recurrence) and the "EGFR not yet tested" gate in Case 001 are
    a CONSTRUCTED demo layer — no public API carries them. They are labeled
    "constructed (illustrative)" in every report and are NOT presented as real.
  * Patient PREFERENCES are deliberately NOT in these charts (a real chart never
    says "prefers not to travel"). They are captured in the Day-5 shared-decision
    form, entered by the patient (doctor-guided).

So: real molecular (cited, traceable) + transparent constructed clinical layer.
The report box stays editable, so a reviewer can paste any report live.
"""

_STUDY = "lgggbm_tcga_pub"
_STUDY_NAME = "Merged Cohort of LGG and GBM — TCGA, Cell 2016 (Ceccarelli et al.)"
_PMID = "26824661"


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


# --- Case 001: real GBM IDH-wildtype (TCGA-02-0033) ---------------------------
# Real curated fields: 54yo Male, glioblastoma, WHO G4, IDH WT, IDHwt subtype,
# MGMT Methylated, ATRX WT (retained). Real mutation call: TP53 R248Q.
# Constructed layer: recurrence, prior Stupp, EGFR "pending" (the verify-catch gate).
CASE_001 = {
    "id": "case-001",
    "label": "Case 001 — 54yo M, glioblastoma IDH-wildtype (TCGA-02-0033)",
    "provenance": _provenance("TCGA-02-0033-01", {
        "IDH_STATUS": "WT", "IDH_CODEL_SUBTYPE": "IDHwt",
        "MGMT_PROMOTER_STATUS": "Methylated", "ATRX_STATUS": "WT (retained)",
        "GRADE": "G4", "HISTOLOGICAL_DIAGNOSIS": "glioblastoma",
        "AGE": "54", "SEX": "Male", "mutations": "TP53 R248Q",
    }),
    "report": """INTEGRATED MOLECULAR PATHOLOGY REPORT

MOLECULAR SOURCE (REAL, de-identified): TCGA-02-0033 · cBioPortal study
lgggbm_tcga_pub (TCGA, Cell 2016; PMID 26824661).
https://www.cbioportal.org/patient?studyId=lgggbm_tcga_pub&caseId=TCGA-02-0033

DEMOGRAPHICS (from TCGA sample): 54-year-old male.

MOLECULAR / GENOMIC (REAL — TCGA curated + variant calls):
- IDH: WILD-TYPE (IDH status: WT; no IDH1 R132 mutation).
- 1p/19q: non-codeleted (IDHwt subtype).
- MGMT promoter: METHYLATED.
- ATRX: retained.
- TP53: mutated — R248Q (somatic variant call).
- Histologic diagnosis (TCGA): glioblastoma, WHO grade 4.

HISTOLOGY (illustrative of the grade-4 glioblastoma label above):
Diffuse astrocytic glioma with MICROVASCULAR PROLIFERATION and NECROSIS.

--- CONSTRUCTED CLINICAL LAYER (illustrative; NOT from TCGA) ---
DISEASE COURSE: right frontal glioblastoma, maximal safe resection; first-line
chemoradiation + adjuvant TEMOZOLOMIDE (Stupp). Now at FIRST RECURRENCE
(measurable enhancing disease, RANO); no therapy yet for this recurrence.
PRIOR TREATMENT: surgery -> radiotherapy -> temozolomide. No prior bevacizumab.
EGFR: NOT YET TESTED — amplification / EGFRvIII status UNKNOWN (pending).
PERFORMANCE STATUS: ECOG 1 (KPS ~80). Location: California.

INTEGRATED DIAGNOSIS:
Glioblastoma, IDH-wildtype, CNS WHO grade 4 — recurrent.
""",
}

# --- Case 002: real IDH-mutant astrocytoma, grade 4 (TCGA-02-2483) -----------
# Real: 43yo Male, IDH Mutant, non-codel, G4, ATRX Mutant (lost), MGMT Methylated,
# TERT WT. Real variant calls: IDH1 R132H, ATRX W2001Cfs*14 (truncating), TP53 R273H.
CASE_002 = {
    "id": "case-002",
    "label": "Case 002 — 43yo M, astrocytoma IDH-mutant grade 4 (TCGA-02-2483)",
    "provenance": _provenance("TCGA-02-2483-01", {
        "IDH_STATUS": "Mutant", "IDH_CODEL_SUBTYPE": "IDHmut-non-codel",
        "MGMT_PROMOTER_STATUS": "Methylated", "TERT_PROMOTER_STATUS": "WT",
        "ATRX_STATUS": "Mutant (loss)", "GRADE": "G4",
        "HISTOLOGICAL_DIAGNOSIS": "glioblastoma (IDH-mutant → astrocytoma grade 4 under WHO CNS5)",
        "AGE": "43", "SEX": "Male",
        "mutations": "IDH1 R132H, ATRX W2001Cfs*14, TP53 R273H",
    }),
    "report": """INTEGRATED MOLECULAR PATHOLOGY REPORT

MOLECULAR SOURCE (REAL, de-identified): TCGA-02-2483 · cBioPortal study
lgggbm_tcga_pub (TCGA, Cell 2016; PMID 26824661).
https://www.cbioportal.org/patient?studyId=lgggbm_tcga_pub&caseId=TCGA-02-2483

DEMOGRAPHICS (from TCGA sample): 43-year-old male.

MOLECULAR / GENOMIC (REAL — TCGA curated + variant calls):
- IDH: MUTANT — IDH1 R132H (somatic variant call).
- 1p/19q: non-codeleted.
- ATRX: LOSS — ATRX W2001Cfs*14 (truncating frameshift).
- TP53: mutated — R273H.
- TERT promoter: wild-type.
- MGMT promoter: METHYLATED.
- Histologic diagnosis (TCGA): grade 4 (high-grade IDH-mutant astrocytic tumor).

HISTOLOGY (illustrative of the grade-4 label above):
Diffuse astrocytoma with microvascular proliferation / necrosis (grade-4 features).

--- CONSTRUCTED CLINICAL LAYER (illustrative; NOT from TCGA) ---
DISEASE COURSE: left temporal diffuse glioma, maximal safe resection; newly
diagnosed, no prior chemoradiation. No prior bevacizumab.
PERFORMANCE STATUS: ECOG 0. Location: New York.

INTEGRATED DIAGNOSIS (WHO CNS5):
Astrocytoma, IDH-mutant, CNS WHO grade 4 (IDH-mutant, 1p/19q non-codeleted,
ATRX-lost; grade 4 by high-grade features).
""",
}

# --- Case 003: real oligodendroglioma, IDH-mut & 1p/19q-codeleted (TCGA-CS-5396)
# Real: 53yo Female, oligodendroglioma, G3, IDH Mutant, codel, TERT Mutant,
# ATRX WT (retained), MGMT Methylated. Real variant calls: IDH1 R132H, TP53 R273H.
CASE_003 = {
    "id": "case-003",
    "label": "Case 003 — 53yo F, oligodendroglioma IDH-mut 1p/19q-codel (TCGA-CS-5396)",
    "provenance": _provenance("TCGA-CS-5396-01", {
        "IDH_STATUS": "Mutant", "IDH_CODEL_SUBTYPE": "IDHmut-codel",
        "MGMT_PROMOTER_STATUS": "Methylated", "TERT_PROMOTER_STATUS": "Mutant",
        "ATRX_STATUS": "WT (retained)", "GRADE": "G3",
        "HISTOLOGICAL_DIAGNOSIS": "oligodendroglioma",
        "AGE": "53", "SEX": "Female", "mutations": "IDH1 R132H, TP53 R273H",
    }),
    "report": """INTEGRATED MOLECULAR PATHOLOGY REPORT

MOLECULAR SOURCE (REAL, de-identified): TCGA-CS-5396 · cBioPortal study
lgggbm_tcga_pub (TCGA, Cell 2016; PMID 26824661).
https://www.cbioportal.org/patient?studyId=lgggbm_tcga_pub&caseId=TCGA-CS-5396

DEMOGRAPHICS (from TCGA sample): 53-year-old female.

MOLECULAR / GENOMIC (REAL — TCGA curated + variant calls):
- IDH: MUTANT — IDH1 R132H (somatic variant call).
- 1p/19q: CO-DELETED (whole-arm loss of 1p and 19q).
- TERT promoter: MUTATED.
- ATRX: retained.
- TP53: mutated — R273H.
- MGMT promoter: METHYLATED.
- Histologic diagnosis (TCGA): oligodendroglioma, WHO grade 3.

HISTOLOGY (illustrative of the label above):
Diffuse glioma with rounded nuclei and perinuclear halos and a delicate
branching capillary pattern.

--- CONSTRUCTED CLINICAL LAYER (illustrative; NOT from TCGA) ---
DISEASE COURSE: right frontal diffuse glioma, gross-total resection. No prior
chemotherapy or radiation. No prior bevacizumab.
PERFORMANCE STATUS: ECOG 0. Location: Illinois.

INTEGRATED DIAGNOSIS (WHO CNS5):
Oligodendroglioma, IDH-mutant and 1p/19q-codeleted, CNS WHO grade 3.
""",
}

# --- Case 004: real GBM IDH-wildtype (TCGA-02-0003), prior-bevacizumab demo ---
# Real: 50yo Male, glioblastoma, G4, IDH WT, MGMT Unmethylated, ATRX WT.
# Real variant calls: EGFR C620Y, TP53 H178Q, TP53 R282W.
# Constructed layer: recurrence + prior bevacizumab (the buried-exclusion demo).
CASE_004 = {
    "id": "case-004",
    "label": "Case 004 — 50yo M, recurrent glioblastoma IDH-wt · prior bevacizumab (TCGA-02-0003)",
    "provenance": _provenance("TCGA-02-0003-01", {
        "IDH_STATUS": "WT", "IDH_CODEL_SUBTYPE": "IDHwt",
        "MGMT_PROMOTER_STATUS": "Unmethylated", "ATRX_STATUS": "WT (retained)",
        "GRADE": "G4", "HISTOLOGICAL_DIAGNOSIS": "glioblastoma",
        "AGE": "50", "SEX": "Male", "mutations": "EGFR C620Y, TP53 H178Q, TP53 R282W",
    }),
    "report": """INTEGRATED MOLECULAR PATHOLOGY REPORT

MOLECULAR SOURCE (REAL, de-identified): TCGA-02-0003 · cBioPortal study
lgggbm_tcga_pub (TCGA, Cell 2016; PMID 26824661).
https://www.cbioportal.org/patient?studyId=lgggbm_tcga_pub&caseId=TCGA-02-0003

DEMOGRAPHICS (from TCGA sample): 50-year-old male.

MOLECULAR / GENOMIC (REAL — TCGA curated + variant calls):
- IDH: WILD-TYPE (IDH status: WT; no IDH1 R132 mutation).
- 1p/19q: non-codeleted (IDHwt subtype).
- MGMT promoter: UNMETHYLATED.
- EGFR: mutated — C620Y (somatic variant call).
- ATRX: retained.
- TP53: mutated — H178Q, R282W.
- Histologic diagnosis (TCGA): glioblastoma, WHO grade 4.

HISTOLOGY (illustrative of the grade-4 glioblastoma label above):
Diffuse astrocytic glioma with MICROVASCULAR PROLIFERATION and NECROSIS.

--- CONSTRUCTED CLINICAL LAYER (illustrative; NOT from TCGA) ---
DISEASE COURSE: left parietal glioblastoma, subtotal resection; first-line
chemoradiation + adjuvant TEMOZOLOMIDE (Stupp). At progression started
BEVACIZUMAB (several cycles); now further progression on bevacizumab, seeking a
trial.
PRIOR TREATMENT: surgery -> radiotherapy -> temozolomide, then BEVACIZUMAB for
recurrence (ongoing until recent progression).
PERFORMANCE STATUS: ECOG 1 (KPS ~80). Location: California.

INTEGRATED DIAGNOSIS:
Glioblastoma, IDH-wildtype, CNS WHO grade 4 — recurrent.
""",
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
