"""Synthetic demo patients — spanning the adult-type diffuse glioma spectrum.

All FULLY SYNTHETIC, authored in-window. No real patient data / no PHI — the
patients are invented; only the trials (pulled live from ClinicalTrials.gov) are
real. Marker combinations reflect real, common molecular patterns (cf. public
TCGA / cBioPortal glioma cohorts); the individuals are not real.

Three distinct cases prove the WHO CNS5 classifier generalizes across the
spectrum (glioblastoma / astrocytoma / oligodendroglioma), not a single canned
demo. The report box is also editable, so a reviewer can type any report live.
"""

CASE_001 = {
    "id": "case-001",
    "label": "Case 001 — 58yo, recurrent GBM (IDH-wildtype), first recurrence",
    "report": """NEURO-ONCOLOGY CASE SUMMARY & MOLECULAR REPORT (synthetic — no PHI)

Patient: 58-year-old female. Glioblastoma, IDH-wildtype. Now at FIRST RECURRENCE.

DISEASE COURSE:
- Initial: right frontal glioblastoma, maximal safe resection.
- First-line: chemoradiation with concurrent + adjuvant TEMOZOLOMIDE (Stupp).
- Now: MRI shows measurable enhancing recurrence (RANO). No prior therapy for
  this recurrence.

HISTOLOGY (initial resection):
Diffuse astrocytic glioma with MICROVASCULAR PROLIFERATION and NECROSIS.
Ki-67 proliferation index ~25%.

MOLECULAR / IHC (from initial resection):
- IDH1 R132H: NEGATIVE (IHC). IDH1/2 sequencing: wild-type.
- MGMT promoter: METHYLATED.
- 1p/19q: intact (no co-deletion).
- EGFR: NOT YET TESTED — amplification / EGFRvIII status UNKNOWN (pending).
- ATRX: retained.
- H3 K27M: not detected.

INTEGRATED DIAGNOSIS:
Glioblastoma, IDH-wildtype, CNS WHO grade 4 — recurrent.

PRIOR TREATMENT:
Surgery -> radiotherapy -> temozolomide (completed first-line).
No prior bevacizumab. No prior therapy for the current recurrence.

CLINICAL / LOGISTICS:
- Performance status: ECOG 1 (KPS ~80).
- Location: California. Prefers to stay in-state; limited caregiver support
  (~2 days/week); wary of earliest-phase (Phase I) experimental studies.
- Open to clinical trial participation.
""",
}

CASE_002 = {
    "id": "case-002",
    "label": "Case 002 — 41yo, astrocytoma, IDH-mutant (grade 4)",
    "report": """NEURO-ONCOLOGY CASE SUMMARY & MOLECULAR REPORT (synthetic — no PHI)

Patient: 41-year-old male. Newly diagnosed left temporal diffuse glioma.

HISTOLOGY (resection):
Diffuse astrocytoma with increased mitotic activity. No microvascular
proliferation. No necrosis identified. Ki-67 ~12%.

MOLECULAR / IHC:
- IDH1 R132H: POSITIVE (IHC). IDH1 mutation confirmed by sequencing.
- ATRX: LOSS of nuclear expression (loss).
- 1p/19q: intact (NO co-deletion).
- TP53: mutated.
- CDKN2A/B: HOMOZYGOUS DELETION present.
- MGMT promoter: unmethylated.
- H3 K27M: not detected.

INTEGRATED DIAGNOSIS:
Astrocytoma, IDH-mutant, CNS WHO grade 4 (CDKN2A/B homozygous deletion).

PRIOR TREATMENT:
Maximal safe resection completed. No prior chemotherapy or radiation.
No prior bevacizumab.

CLINICAL / LOGISTICS:
- Performance status: ECOG 0.
- Location: New York. Willing to travel for the right trial.
- Open to clinical trial participation.
""",
}

CASE_003 = {
    "id": "case-003",
    "label": "Case 003 — 35yo, oligodendroglioma, IDH-mutant & 1p/19q-codeleted",
    "report": """NEURO-ONCOLOGY CASE SUMMARY & MOLECULAR REPORT (synthetic — no PHI)

Patient: 35-year-old female. Right frontal diffuse glioma, slow-growing.

HISTOLOGY (resection):
Diffuse glioma with rounded nuclei and perinuclear halos ("fried-egg") and a
delicate branching capillary pattern. Low mitotic activity. No microvascular
proliferation. No necrosis. Ki-67 ~5%.

MOLECULAR / IHC:
- IDH1 R132H: POSITIVE (IHC). IDH1 mutation confirmed.
- 1p/19q: CO-DELETED (whole-arm loss of 1p and 19q).
- ATRX: retained.
- TERT promoter: mutated (C228T).
- CDKN2A/B: retained (no homozygous deletion).
- MGMT promoter: methylated.
- H3 K27M: not detected.

INTEGRATED DIAGNOSIS:
Oligodendroglioma, IDH-mutant and 1p/19q-codeleted, CNS WHO grade 2.

PRIOR TREATMENT:
Gross-total resection. No prior chemotherapy or radiation. No prior bevacizumab.

CLINICAL / LOGISTICS:
- Performance status: ECOG 0.
- Location: Illinois. Interested in trials but prioritizes quality of life.
- Open to clinical trial participation.
""",
}

SYNTHETIC_PATIENTS = [CASE_001, CASE_002, CASE_003]

# Default patient (used where a single case is needed, e.g. extract/classify defaults).
SYNTHETIC_PATIENT = CASE_001

_BY_ID = {p["id"]: p for p in SYNTHETIC_PATIENTS}


def get_patient(patient_id: str | None):
    """Return a patient by id, or the default case if id is missing/unknown."""
    if patient_id and patient_id in _BY_ID:
        return _BY_ID[patient_id]
    return SYNTHETIC_PATIENT
