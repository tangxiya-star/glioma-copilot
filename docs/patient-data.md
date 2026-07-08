# Demo patient data — full table, with sources

> This is the **exact data behind the 8 demo patients** in the Patient panel, so it can be inspected without running the app. Generated from `/api/patients`. It documents every field, its **source**, and whether it is **REAL** (from a public de-identified source) or **CONSTRUCTED** (illustrative, authored — no public source).

## Sources

| Source | What it provides | Access |
|---|---|---|
| **cBioPortal** — study `lgggbm_tcga_pub` (TCGA, *Cell* 2016, PMID 26824661) | molecular markers + variant calls; age, sex, KPS | public, de-identified, no key |
| **NIH GDC** (`api.gdc.cancer.gov`) | prior treatment (agents), tumor site, primary diagnosis, disease status (`classification_of_tumor`), resection type (`method_of_diagnosis`) | public, de-identified |
| **RxNorm (RxNav) + ChEMBL** | canonical drug identity (RxCUI/ingredient) + mechanism/class | public, no key |
| **CONSTRUCTED** (authored) | steroid dose, precise sub-lobar location; Case-001 EGFR-pending gate | illustrative — NOT from any source |

## Field → source / real-vs-constructed

| Field | Source | Real / Constructed |
|---|---|---|
| Age, Sex | cBioPortal (patient) | REAL |
| Histology / diagnosis | cBioPortal + GDC | REAL |
| IDH, 1p/19q, MGMT, ATRX, TERT, Grade | cBioPortal | REAL |
| Variant calls (IDH1/TP53/EGFR/ATRX…) | cBioPortal mutations API | REAL |
| KPS (performance status) | cBioPortal `KARNOFSKY_PERFORMANCE_SCORE` | REAL |
| Tumor site (coarse) | GDC `site_of_resection_or_biopsy` | REAL |
| Disease status (newly-dx / recurrent) | GDC `classification_of_tumor` | REAL |
| Resection type (resection / biopsy) | GDC `method_of_diagnosis` | REAL |
| Prior therapy (drug agents) | GDC `diagnoses.treatments` | REAL |
| Drug identity + mechanism | RxNorm + ChEMBL | REAL (derived) |
| Steroid dose | — (no public source) | **CONSTRUCTED** |
| Precise location (lobe/side) | — (GDC only coarse 'Brain, NOS') | **CONSTRUCTED** |
| Case-001 EGFR amplification 'not yet tested' gate | — (not in cBioPortal fields) | **CONSTRUCTED** (verify-catch demo) |

## The 8 patients

| # | Case id | TCGA sample | Age/Sex | Diagnosis | IDH | 1p/19q | MGMT | ATRX | Grade | KPS | Site | Status | Resection | Steroid ᶜ | Location ᶜ | Prior therapy (real, GDC) | Variant calls (real) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | case-001 | TCGA-06-6695-01 | 64/M | glioblastoma | WT | IDHwt | Methylated | WT (retained) | G4 | 40 | Brain, NOS | Newly diagnosed | Surgical resection | Dexamethasone 4 mg/day | Right frontal, supratentorial | temozolomide, radiation (external beam) | none reported in IDH1/ATRX/TERT/EGFR/TP53 panel |
| 2 | case-002 | TCGA-02-2483-01 | 43/M | glioblastoma | Mutant | IDHmut-non-codel | Methylated | Mutant (loss) | G4 | 80 | Brain, NOS | Newly diagnosed | Biopsy | None | Left temporal, supratentorial | temozolomide, radiation (external beam) | IDH1 R132H, ATRX W2001Cfs*14, TP53 R273H |
| 3 | case-003 | TCGA-CS-5396-01 | 53/F | oligodendroglioma | Mutant | IDHmut-codel | Methylated | WT (retained) | G3 | 90 | Nervous system, NOS | Newly diagnosed | — | None | Right frontal, supratentorial | temozolomide, radiation (external beam) | IDH1 R132H, TP53 R273H |
| 4 | case-004 | TCGA-06-5413-01 | 67/M | glioblastoma | WT | IDHwt | Unmethylated | WT (retained) | G4 | 60 | Brain, NOS | Newly diagnosed | Surgical resection | Dexamethasone 2 mg/day | Left parietal, supratentorial | temozolomide, bevacizumab, radiation (external beam) | none reported in IDH1/ATRX/TERT/EGFR/TP53 panel |
| 5 | live-TCGA-06-6700 | TCGA-06-6700-01 | 76/M | glioblastoma | WT | IDHwt | Methylated | WT | G4 | 100 | Brain, NOS | Newly diagnosed | Surgical resection | — | — | radiation, external beam, temozolomide, vandetanib | none reported in IDH1/ATRX/TERT/EGFR/TP53 panel |
| 6 | live-TCGA-14-1450 | TCGA-14-1450-01 | 57/F | glioblastoma | WT | IDHwt | Methylated | WT | G4 | 80 | Not Reported | Recurrent | — | — | — | bevacizumab, dexamethasone, pharmaceutical therapy, nos, radiation, external beam, temozolomide | none reported in IDH1/ATRX/TERT/EGFR/TP53 panel |
| 7 | live-TCGA-CS-6668 | TCGA-CS-6668-01 | 57/F | oligodendroglioma | Mutant | IDHmut-codel | Methylated | WT | G2 | 90 | Nervous system, NOS | Newly diagnosed | — | — | — | temozolomide | IDH1 R132H |
| 8 | live-TCGA-DB-5273 | TCGA-DB-5273-01 | 33/M | astrocytoma | Mutant | IDHmut-non-codel | Unmethylated | Mutant | G3 | — | Nervous system, NOS | Newly diagnosed | — | — | — | antiseizure treatment, radiation, external beam, temozolomide | ATRX Q262*, IDH1 R132H, TP53 R273H |

ᶜ = constructed (illustrative, not from public data). Everything else is REAL and traceable to the source below.

## Provenance links (click to verify)

- **case-001** (TCGA-06-6695-01): [cBioPortal molecular](https://www.cbioportal.org/patient?studyId=lgggbm_tcga_pub&caseId=TCGA-06-6695) · [NIH GDC treatment/clinical](https://portal.gdc.cancer.gov/cases/0628cb4a-c480-4b2f-bd2e-bb33e6994302)
- **case-002** (TCGA-02-2483-01): [cBioPortal molecular](https://www.cbioportal.org/patient?studyId=lgggbm_tcga_pub&caseId=TCGA-02-2483) · [NIH GDC treatment/clinical](https://portal.gdc.cancer.gov/cases/a2ac9937-f351-4d78-9261-264bf6c21e0c)
- **case-003** (TCGA-CS-5396-01): [cBioPortal molecular](https://www.cbioportal.org/patient?studyId=lgggbm_tcga_pub&caseId=TCGA-CS-5396) · [NIH GDC treatment/clinical](https://portal.gdc.cancer.gov/cases/b6c2c9bd-625b-4a98-830c-49c344f6cb5f)
- **case-004** (TCGA-06-5413-01): [cBioPortal molecular](https://www.cbioportal.org/patient?studyId=lgggbm_tcga_pub&caseId=TCGA-06-5413) · [NIH GDC treatment/clinical](https://portal.gdc.cancer.gov/cases/8d2e88d9-d8d0-4c42-8aa2-205a788dea58)
- **live-TCGA-06-6700** (TCGA-06-6700-01): [cBioPortal molecular](https://www.cbioportal.org/patient?studyId=lgggbm_tcga_pub&caseId=TCGA-06-6700) · [NIH GDC treatment/clinical](https://portal.gdc.cancer.gov/cases/3dddfc44-7bb1-4974-8a65-a84fd4bac484)
- **live-TCGA-14-1450** (TCGA-14-1450-01): [cBioPortal molecular](https://www.cbioportal.org/patient?studyId=lgggbm_tcga_pub&caseId=TCGA-14-1450) · [NIH GDC treatment/clinical](https://portal.gdc.cancer.gov/cases/f2ec3b94-cb92-4335-bdf9-02c046130bab)
- **live-TCGA-CS-6668** (TCGA-CS-6668-01): [cBioPortal molecular](https://www.cbioportal.org/patient?studyId=lgggbm_tcga_pub&caseId=TCGA-CS-6668) · [NIH GDC treatment/clinical](https://portal.gdc.cancer.gov/cases/a5d3f3fb-6541-419d-b47e-720d438f1bff)
- **live-TCGA-DB-5273** (TCGA-DB-5273-01): [cBioPortal molecular](https://www.cbioportal.org/patient?studyId=lgggbm_tcga_pub&caseId=TCGA-DB-5273) · [NIH GDC treatment/clinical](https://portal.gdc.cancer.gov/cases/ae2db022-eb4f-4b65-89b6-9fd4439ddeef)

---
*All 8 are TCGA patients recorded ALIVE; survival/vital status is never fetched or shown. No non-public / non-consented patient data is used (see PRD §12.5).*