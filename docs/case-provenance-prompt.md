# Claude Science prompt — traceable / QC'd version of the 8 demo cases

> Paste into **Claude Science → "Run a first-pass analysis on a dataset you already have"**.
> The 8 cases' REAL values are embedded below and are the ground truth — Claude Science
> must **verify, annotate provenance, and QC**, NOT regenerate/invent data.
>
> Source of every field (already true, from public de-identified sources):
> - **cBioPortal** (`lgggbm_tcga_pub`, TCGA, Cell 2016 PMID 26824661): age, sex, KPS, IDH,
>   1p/19q, MGMT, ATRX, TERT, grade, variant calls
> - **NIH GDC** (`api.gdc.cancer.gov`): prior therapy, tumor site, disease status, resection type
> - **RxNorm + ChEMBL**: drug identity + mechanism
> - **CONSTRUCTED** (no public source, must stay labeled): steroid dose, precise sub-lobar
>   location, Case-001's "EGFR not-yet-tested" gate
>
> After it runs: save the JSON as `docs/case-provenance.json`; spot-check a couple of cases
> against their cBioPortal + GDC links; the constructed fields must remain flagged.

---

## PASTE THIS INTO CLAUDE SCIENCE

You are a data-provenance and QC analyst for a glioma clinical-trial copilot. Below is the EXACT dataset behind 8 demo patients. Every molecular and clinical value is REAL, already pulled from public de-identified sources (cBioPortal for molecular + age/sex/KPS; NIH GDC for prior therapy / tumor site / disease status / resection type; RxNorm+ChEMBL for drug mechanism). A few fields are CONSTRUCTED (no public source) and are marked.

**Your job is to VERIFY, ANNOTATE PROVENANCE, and QC this data — NOT to regenerate, guess, or "improve" any value. Never invent a value. If a field is missing (null), keep it missing.** Treat the numbers/calls below as ground truth; if you independently check a public source and find a discrepancy, REPORT it in `qc_flags`, do not overwrite.

Produce, for each case, a traceable record, and then a cohort-level summary. Specifically:

1. **Per-field provenance.** For every field, tag its `source` (one of: cBioPortal, GDC, RxNorm+ChEMBL, CONSTRUCTED) and the `source_url` (the case's cBioPortal or GDC link given below; empty for constructed). Mark `real_or_constructed`.
2. **WHO CNS5 consistency QC (the key analysis).** For each case, derive the integrated **2021 WHO CNS5** diagnosis from its molecular profile (IDH → then 1p/19q for oligodendroglioma vs astrocytoma; molecular grade-4 criteria: CDKN2A/B for IDH-mutant astrocytoma; TERT / EGFR-amp / +7-10 for IDH-wildtype). Compare it to the `source_histology` (the TCGA-era histological label). Where the 2021 reclassification changes the diagnosis, flag it explicitly (e.g. an IDH-**mutant** tumor labeled "glioblastoma" in TCGA is, by WHO CNS5, **Astrocytoma, IDH-mutant** — glioblastoma is IDH-wildtype only). State `who_cns5_diagnosis`, whether it `matches_source_histology`, and the reasoning.
3. **Internal-consistency flags.** Note any molecular contradiction (e.g. IDH-mutant + 1p/19q-codeleted must be oligodendroglioma; ATRX loss should not co-occur with 1p/19q codeletion; a variant call that conflicts with a summary marker).
4. **Provenance completeness.** Flag any REAL field lacking a source link, and confirm every CONSTRUCTED field is labeled.
5. **Cohort summary.** Spectrum coverage (how many of each WHO CNS5 entity), marker distribution (IDH mut vs wt, MGMT, codeletion), and how many cases the 2021 reclassification changes vs the TCGA histology. (If you can render a figure, show the entity + marker distribution — but never any survival/vital-status content; it is intentionally absent.)

**Rules:** Do not fabricate values, sources, or citations. Do not surface or infer survival / vital status (absent by design). Keep every constructed field flagged. Output ONLY one valid JSON object matching the schema below — no prose outside it.

**Output JSON schema:**

```json
{
  "cohort_summary": {
    "n": 8,
    "who_cns5_entities": {"glioblastoma_idhwt": 0, "astrocytoma_idhmut": 0, "oligodendroglioma": 0},
    "reclassified_by_2021": 0,
    "marker_distribution": {"idh_mutant": 0, "idh_wildtype": 0, "mgmt_methylated": 0, "codeleted_1p19q": 0},
    "notes": "string"
  },
  "cases": [
    {
      "case_id": "string",
      "tcga_sample": "string",
      "provenance": {"cbioportal": "url", "gdc": "url"},
      "fields": [
        {"field": "idh", "value": "string_or_null", "source": "cBioPortal|GDC|RxNorm+ChEMBL|CONSTRUCTED", "source_url": "string", "real_or_constructed": "real|constructed"}
      ],
      "who_cns5": {
        "who_cns5_diagnosis": "string",
        "source_histology": "string",
        "matches_source_histology": true,
        "reclassified_by_2021": false,
        "reasoning": "string"
      },
      "qc_flags": ["string"]
    }
  ]
}
```

Return the JSON object only.

**DATASET (ground truth — verify/annotate, do not alter):**

```json
[
 {"case_id":"case-001","tcga_sample":"TCGA-06-6695-01","age":64,"sex":"M","source_histology":"glioblastoma","idh":"wildtype","codel_1p19q":"IDHwt","mgmt":"methylated","atrx":"retained","tert":null,"grade":"G4","kps":40,"site":"Brain, NOS","status":"newly diagnosed","resection":"surgical resection","prior_therapy":["temozolomide","radiation (external beam)"],"variants":[],"steroid_constructed":"Dexamethasone 4 mg/day","location_constructed":"Right frontal, supratentorial","special_constructed":"EGFR amplification 'not yet tested' gate (verify-catch demo)","cbioportal":"https://www.cbioportal.org/patient?studyId=lgggbm_tcga_pub&caseId=TCGA-06-6695","gdc":"https://portal.gdc.cancer.gov/cases/0628cb4a-c480-4b2f-bd2e-bb33e6994302"},
 {"case_id":"case-002","tcga_sample":"TCGA-02-2483-01","age":43,"sex":"M","source_histology":"glioblastoma","idh":"mutant","codel_1p19q":"IDHmut-non-codel","mgmt":"methylated","atrx":"loss","tert":null,"grade":"G4","kps":80,"site":"Brain, NOS","status":"newly diagnosed","resection":"biopsy","prior_therapy":["temozolomide","radiation (external beam)"],"variants":["IDH1 R132H","ATRX W2001Cfs*14","TP53 R273H"],"steroid_constructed":null,"location_constructed":"Left temporal, supratentorial","cbioportal":"https://www.cbioportal.org/patient?studyId=lgggbm_tcga_pub&caseId=TCGA-02-2483","gdc":"https://portal.gdc.cancer.gov/cases/a2ac9937-f351-4d78-9261-264bf6c21e0c"},
 {"case_id":"case-003","tcga_sample":"TCGA-CS-5396-01","age":53,"sex":"F","source_histology":"oligodendroglioma","idh":"mutant","codel_1p19q":"IDHmut-codel","mgmt":"methylated","atrx":"retained","tert":null,"grade":"G3","kps":90,"site":"Nervous system, NOS","status":"newly diagnosed","resection":null,"prior_therapy":["temozolomide","radiation (external beam)"],"variants":["IDH1 R132H","TP53 R273H"],"steroid_constructed":null,"location_constructed":"Right frontal, supratentorial","cbioportal":"https://www.cbioportal.org/patient?studyId=lgggbm_tcga_pub&caseId=TCGA-CS-5396","gdc":"https://portal.gdc.cancer.gov/cases/b6c2c9bd-625b-4a98-830c-49c344f6cb5f"},
 {"case_id":"case-004","tcga_sample":"TCGA-06-5413-01","age":67,"sex":"M","source_histology":"glioblastoma","idh":"wildtype","codel_1p19q":"IDHwt","mgmt":"unmethylated","atrx":"retained","tert":null,"grade":"G4","kps":60,"site":"Brain, NOS","status":"newly diagnosed","resection":"surgical resection","prior_therapy":["temozolomide","bevacizumab","radiation (external beam)"],"variants":[],"steroid_constructed":"Dexamethasone 2 mg/day","location_constructed":"Left parietal, supratentorial","cbioportal":"https://www.cbioportal.org/patient?studyId=lgggbm_tcga_pub&caseId=TCGA-06-5413","gdc":"https://portal.gdc.cancer.gov/cases/8d2e88d9-d8d0-4c42-8aa2-205a788dea58"},
 {"case_id":"live-TCGA-06-6700","tcga_sample":"TCGA-06-6700-01","age":76,"sex":"M","source_histology":"glioblastoma","idh":"wildtype","codel_1p19q":"IDHwt","mgmt":"methylated","atrx":"WT","tert":null,"grade":"G4","kps":100,"site":"Brain, NOS","status":"newly diagnosed","resection":"surgical resection","prior_therapy":["radiation (external beam)","temozolomide","vandetanib"],"variants":[],"cbioportal":"https://www.cbioportal.org/patient?studyId=lgggbm_tcga_pub&caseId=TCGA-06-6700","gdc":"https://portal.gdc.cancer.gov/cases/3dddfc44-7bb1-4974-8a65-a84fd4bac484"},
 {"case_id":"live-TCGA-14-1450","tcga_sample":"TCGA-14-1450-01","age":57,"sex":"F","source_histology":"glioblastoma","idh":"wildtype","codel_1p19q":"IDHwt","mgmt":"methylated","atrx":"WT","tert":null,"grade":"G4","kps":80,"site":"Not Reported","status":"recurrent","resection":null,"prior_therapy":["bevacizumab","dexamethasone","radiation (external beam)","temozolomide"],"variants":[],"cbioportal":"https://www.cbioportal.org/patient?studyId=lgggbm_tcga_pub&caseId=TCGA-14-1450","gdc":"https://portal.gdc.cancer.gov/cases/f2ec3b94-cb92-4335-bdf9-02c046130bab"},
 {"case_id":"live-TCGA-CS-6668","tcga_sample":"TCGA-CS-6668-01","age":57,"sex":"F","source_histology":"oligodendroglioma","idh":"mutant","codel_1p19q":"IDHmut-codel","mgmt":"methylated","atrx":"WT","tert":null,"grade":"G2","kps":90,"site":"Nervous system, NOS","status":"newly diagnosed","resection":null,"prior_therapy":["temozolomide"],"variants":["IDH1 R132H"],"cbioportal":"https://www.cbioportal.org/patient?studyId=lgggbm_tcga_pub&caseId=TCGA-CS-6668","gdc":"https://portal.gdc.cancer.gov/cases/a5d3f3fb-6541-419d-b47e-720d438f1bff"},
 {"case_id":"live-TCGA-DB-5273","tcga_sample":"TCGA-DB-5273-01","age":33,"sex":"M","source_histology":"astrocytoma","idh":"mutant","codel_1p19q":"IDHmut-non-codel","mgmt":"unmethylated","atrx":"mutant","tert":null,"grade":"G3","kps":null,"site":"Nervous system, NOS","status":"newly diagnosed","resection":null,"prior_therapy":["radiation (external beam)","temozolomide","antiseizure treatment"],"variants":["ATRX Q262*","IDH1 R132H","TP53 R273H"],"cbioportal":"https://www.cbioportal.org/patient?studyId=lgggbm_tcga_pub&caseId=TCGA-DB-5273","gdc":"https://portal.gdc.cancer.gov/cases/ae2db022-eb4f-4b65-89b6-9fd4439ddeef"}
]
```
