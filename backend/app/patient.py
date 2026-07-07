"""The synthetic demo patient — Case 001, aligned to docs/demo_data_pack.md.

Fully SYNTHETIC and authored in-window. No real patient data / no PHI — the
patient is invented; only the trials (pulled live from ClinicalTrials.gov) are
real. The profile is deliberately built so that:
  - it cleanly matches a real in-state trial (NCT05432804, Selinexor + TMZ), and
  - EGFR is UNKNOWN (not yet tested), which gates the EGFR-targeted trials
    (NCT07089641 ERAS-801, NCT07209241 CAR-T) and creates the ambiguity the
    verification agent must catch ("possibly relevant; requires EGFR testing").

The marker combination (GBM IDH-wildtype + MGMT-methylated) is a real, common
GBM molecular pattern (cf. public TCGA/cBioPortal GBM cohorts); the individual
is not.
"""

SYNTHETIC_PATIENT = {
    "id": "case-001",
    "label": "Case 001 — 58yo, recurrent GBM (IDH-wildtype), first recurrence",
    "report": """NEURO-ONCOLOGY CASE SUMMARY & MOLECULAR REPORT (synthetic — no PHI)

Patient: 58-year-old female. Glioblastoma, IDH-wildtype. Now at FIRST RECURRENCE.

DISEASE COURSE:
- Initial: right frontal glioblastoma, maximal safe resection.
- First-line: chemoradiation with concurrent + adjuvant TEMOZOLOMIDE (Stupp).
- Now: MRI shows measurable enhancing recurrence (RANO). No prior therapy for
  this recurrence.

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
