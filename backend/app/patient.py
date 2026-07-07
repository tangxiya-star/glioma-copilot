"""A single synthetic glioma patient — the flagship demo case (GBM, IDH-wildtype).

Fully synthetic, authored in-window. No real patient data. Used to drive the
end-to-end flow before any paste-your-own-report UI exists.
"""

SYNTHETIC_PATIENT = {
    "id": "demo-gbm-01",
    "label": "Demo case — 58yo, newly diagnosed glioblastoma",
    "report": """NEUROPATHOLOGY & MOLECULAR REPORT (synthetic)

Patient: 58-year-old male. Right temporal lobe mass, gross-total resection.

HISTOLOGY:
Diffuse astrocytic glioma with microvascular proliferation and palisading
necrosis. Ki-67 proliferation index ~28%.

MOLECULAR / IHC:
- IDH1 R132H: NEGATIVE (immunohistochemistry). IDH1/2 sequencing: wild-type.
- MGMT promoter: METHYLATED.
- 1p/19q: intact (no co-deletion).
- EGFR: amplified; EGFRvIII rearrangement detected.
- TERT promoter: mutated (C228T).
- ATRX: retained.
- CDKN2A/B: homozygous deletion present.
- H3 K27M: not detected.

INTEGRATED DIAGNOSIS (per treating pathologist):
Glioblastoma, IDH-wildtype, CNS WHO grade 4.

PRIOR TREATMENT:
Maximal safe resection completed. No prior chemotherapy or radiation to date.
No prior bevacizumab.

CLINICAL:
KPS 90. No significant comorbidities. Candidate for standard chemoradiation and
open to clinical trial participation.
""",
}
