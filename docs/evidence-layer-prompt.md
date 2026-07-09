# Claude Science master prompt — Glioma evidence layer

> Paste the block below into **Claude Science → "Map the recent literature of your subfield"**.
> It generates the **cited evidence layer** that sits on top of the app's scraped fact layer
> (ClinicalTrials.gov / cBioPortal / GDC / RxNorm / ChEMBL). Output is a single JSON object
> matching the schema, ingested by the backend as `/api/evidence`.
>
> **Honesty rails baked in:** every claim needs a real citation or is marked `unsourced`
> (never a fabricated PMID); prognosis is population-level only, never individual; conflicting
> evidence is flagged. After it runs, **spot-check the PMIDs** and pass the briefs through the
> app's verify agent before shipping.
>
> Before running: replace `<<DEMO_NCT_IDS>>` with your actual demo trial NCT numbers
> (or delete the `trial_rationale` instruction to run the trial-agnostic library first).

---

## PASTE THIS INTO CLAUDE SCIENCE

You are building a **cited evidence library** for a clinician-facing **glioma clinical-trial evidence-review copilot**. The app already holds real, scraped *facts* (trials + eligibility text from ClinicalTrials.gov, molecular calls from cBioPortal, treatment/status from NIH GDC, drug mechanism from RxNorm/ChEMBL). Your job is the *interpretation* layer on top: **why each fact matters for trial eligibility, with a real citation for every claim.**

**Scope:** 2021 **WHO CNS5 adult-type diffuse gliomas — the WHOLE spectrum, not only glioblastoma**: (a) Glioblastoma, IDH-wildtype (grade 4); (b) Astrocytoma, IDH-mutant (grades 2–4); (c) Oligodendroglioma, IDH-mutant and 1p/19q-codeleted (grades 2–3).

**Produce, with a real citation attached to every factual claim:**

- **(A) Diagnostic entities** — for each of the three entities: defining molecular features, how WHO CNS5 classifies it, and its clinical/prognostic significance.
- **(B) Biomarkers** — for each of: IDH1/IDH2, MGMT promoter methylation, EGFR (incl. EGFRvIII / amplification), 1p/19q codeletion, ATRX, TP53, TERT promoter, CDKN2A/B homozygous deletion — what it is, its clinical significance, its role in **trial eligibility** (inclusion / exclusion / stratification / prognostic), how it typically appears in eligibility text, and the assay methods used to test it.
- **(C) Drug-class exclusions** — mechanism classes that commonly appear as exclusion criteria in glioma trials (at minimum: anti-VEGF / VEGF-A inhibitors, e.g. bevacizumab), the example drugs, why they are excluded, and typical criterion wording.
- **(D) Population prognosis** — for each entity, the **population-level** survival range under standard care, with key modifiers (e.g. MGMT status). **This is a population range with uncertainty, explicitly NOT an individual prediction** — say so in every entry.
- **(E) Trial rationale** — for each of these trials NCT05432804 (Selinexor + Temozolomide for recurrent GBM), NCT07089641 (ERAS-801, an EGFR inhibitor, for progressive/recurrent GBM), NCT07209241 (CART-EGFR-IL13Ralpha2 CAR-T cells for recurrent GBM): the target/mechanism, the scientific rationale, and the landmark evidence supporting it.

**Hard rules (this app's entire value is trustworthiness — obey exactly):**

1. **Never fabricate a citation.** Attach a real PMID/DOI or a named authoritative source (e.g. "WHO CNS5 2021", "NCCN CNS Cancers", "EANO guideline") to each claim. If you cannot find a real source for a claim, set its citation to `null`, set `confidence` to `"unsourced"`, and keep the claim short — do **not** invent an identifier. Prefer recent literature (last ~5 years) but include landmark older papers where they are the primary evidence.
2. **Flag conflicting or evolving evidence** in `uncertainty_notes` rather than presenting one side as settled.
3. **Prognosis is population-level only.** No individual survival prediction, and never reference any individual patient's outcome or vital status.
4. Keep each text field concise and clinician-facing (roughly 1–4 sentences).
5. **Output ONLY one valid JSON object** matching the schema below — no prose before or after.

**Output JSON schema:**

```json
{
  "meta": {
    "scope": "WHO CNS5 adult-type diffuse glioma",
    "generation_method": "Claude Science literature map",
    "disclaimer": "Cited evidence synthesis for clinician review; not a source of truth and not medical advice. Prognosis figures are population ranges, not individual predictions."
  },
  "entities": [
    {
      "id": "gbm_idhwt",
      "who_cns5_name": "Glioblastoma, IDH-wildtype",
      "who_grade": 4,
      "defining_molecular_features": ["string"],
      "classification_basis": "string",
      "clinical_significance": "string",
      "confidence": "established | emerging | unsourced",
      "uncertainty_notes": "string",
      "citations": [{"pmid": "string_or_null", "doi": "string_or_null", "source": "string", "title": "string", "year": 0}]
    }
  ],
  "biomarkers": [
    {
      "id": "mgmt",
      "name": "MGMT promoter methylation",
      "what_it_is": "string",
      "clinical_significance": "string",
      "eligibility_role": "inclusion | exclusion | stratification | prognostic",
      "eligibility_notes": "how it typically appears in glioma trial eligibility text",
      "assay_methods": ["string"],
      "relevant_entities": ["gbm_idhwt"],
      "confidence": "established | emerging | unsourced",
      "uncertainty_notes": "string",
      "citations": [{"pmid": "string_or_null", "doi": "string_or_null", "source": "string", "title": "string", "year": 0}]
    }
  ],
  "drug_class_exclusions": [
    {
      "id": "anti_vegf",
      "mechanism_class": "VEGF-A inhibitor",
      "example_drugs": ["bevacizumab"],
      "why_excluded": "string",
      "typical_criterion_wording": ["prior anti-VEGF therapy"],
      "confidence": "established | emerging | unsourced",
      "citations": [{"pmid": "string_or_null", "doi": "string_or_null", "source": "string", "title": "string", "year": 0}]
    }
  ],
  "population_prognosis": [
    {
      "entity_id": "gbm_idhwt",
      "measure": "median overall survival under standard care",
      "population_range": "string (a range, e.g. '~14-16 months')",
      "modifiers": ["string"],
      "is_population_level": true,
      "not_for_individual_prediction": true,
      "uncertainty_notes": "string",
      "citations": [{"pmid": "string_or_null", "doi": "string_or_null", "source": "string", "title": "string", "year": 0}]
    }
  ],
  "trial_rationale": [
    {
      "nct_id": "string",
      "target_or_mechanism": "string",
      "scientific_rationale": "string",
      "landmark_evidence": ["string"],
      "confidence": "established | emerging | unsourced",
      "citations": [{"pmid": "string_or_null", "doi": "string_or_null", "source": "string", "title": "string", "year": 0}]
    }
  ]
}
```

Return the JSON object only.

---

## After it returns

1. **Spot-check citations.** Open a few PMIDs on PubMed — confirm they exist and say what the brief claims. Delete/mark any that don't check out. (LLMs hallucinate citations; this app's credibility depends on catching that.)
2. Save the JSON as `backend/app/evidence.json`.
3. Backend reads it; Investigation view surfaces the matching entity/biomarker/drug-class/prognosis brief + citation links when a trial is assessed.
4. Optionally run the JSON's text briefs through the app's existing **verify agent** as a second self-check before the demo.
