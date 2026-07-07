# Glioma Trial & Report Copilot — PRD (leaner draft)

> One of two PRDs kept in this repo. This is the **leaner draft** — clinician-primary, "one engine, two views", focused on trial-eligibility screening, with a compact architecture write-up. The **fuller / most complete PRD** is `PRD-v2-full.md` (evidence review & shared decision framing). Both reflect the same product; keep whichever framing is more useful for the task at hand.
>
> Reframed after domain-expert feedback: **expand from recurrent GBM to the whole glioma population; the molecular report is the core; treatment is fixed so we don't touch it.** Primary user is the **clinician / trial coordinator** (accelerate their workflow); the patient/family are served by a second view of the same engine.

---

## 1. Product name

**Glioma Copilot** — a molecular-report-driven trial-eligibility and comprehension assistant for neuro-oncology teams and their patients.

## 2. One-liner

A clinician pastes a glioma molecular pathology report; the copilot returns the correct 2021 WHO classification and an instant, source-grounded, per-criterion eligibility screen against recruiting trials (met / not-met / needs-testing) — collapsing hours of manual screening into seconds — and renders the same verified analysis in plain language for the patient conversation.

---

## 3. Problem statement

Glioma care is molecularly complex, and since the **2021 WHO CNS5 reclassification** the diagnosis is defined by molecular markers, not histology alone. This creates two real, distinct pains:

- **Clinician workflow (primary).** For a given patient, deciding which trials are relevant and whether they qualify means manually reading long, dense inclusion/exclusion criteria and checking each against the patient's molecular + clinical profile. This is slow, repetitive, and error-prone — a documented burden for neuro-oncologists and trial coordinators.
- **Patient comprehension (secondary).** Families without a medical background cannot read the molecular report or the eligibility criteria, and cannot tell what their subtype means.

What is **not** the pain, and what we deliberately avoid:
- **Choosing treatment** — the backbone (surgery → chemoradiation → maintenance) is largely fixed. We don't build treatment decision support.
- **Sponsors finding patients** — molecular registries already let trial sponsors find suitable patients; that's a funding problem, not a discovery one. Our direction is the reverse and per-patient: *given this clinician's patient, which trials, and do they qualify.*

> Distinction that matters: an expert clinician can read a report; the burden is the *volume* of eligibility screening. A non-expert family can't read anything; the burden is *comprehension*. One verified engine serves both.

---

## 4. Approach (how we solve it)

One Claude-centered, **source-grounded and self-verifying** engine, surfaced as two views:

1. **Ingest** a molecular pathology report (+ optional clinical context: age, prior treatment, location).
2. **Classify** per WHO CNS5 (2021) from the molecular markers; flag when an older label (e.g. "GBM") is now reclassified.
3. **Retrieve** relevant recruiting trials (glioma-wide) from ClinicalTrials.gov (live).
4. **Screen eligibility per criterion**: for each trial, translate every inclusion/exclusion criterion into **met / not-met / unknown (needs test X)**, each cited to the eligibility text; handle negation ("no prior bevacizumab").
5. **Verify (core differentiator)**: an independent agent checks every claim (classification, eligibility, any prognosis context) against source records and rewrites overstatements (e.g. "eligible for Trial B" → "possibly eligible; requires EGFR testing to confirm").
6. **Render two views** of the same verified result:
   - **Clinician view** — the dense, actionable eligibility screen + WHO classification + citations + verification log.
   - **Patient view** — a plain-language rendering (one additional translation step) of the same verified analysis + what participation involves + questions to ask the care team.

**Governing principle**: Claude is not the source of truth. It reasons only over retrieved authoritative records; every claim is traceable and verifiable. This is decision support, not diagnosis, treatment recommendation, or survival prediction.

---

## 5. Target users

- **Primary: neuro-oncologist / clinical trial coordinator.** Needs to cut the time spent screening trial eligibility per patient, with results they can trust and act on.
- **Secondary: glioma patient & family.** Need the same analysis in plain language for the shared conversation.

## 6. Goals

1. Collapse manual per-patient trial-eligibility screening from hours to seconds.
2. Give the correct current (WHO CNS5 2021) classification from the molecular report.
3. Screen each trial per criterion (met / not-met / unknown), every claim source-cited.
4. Ground and verify every claim; catch and rewrite overstatements.
5. Render a plain-language patient view from the same verified result.
6. Support — never replace — clinical judgment.

## 7. Non-goals

- Not a diagnosis — classification must be confirmed by a pathologist.
- No treatment recommendation (the backbone is fixed).
- **No individual survival prediction** — prognosis, if shown, is a sourced population range with explicit uncertainty.
- No autonomous trial enrollment; no direct medical advice to patients.
- Does not replace clinician judgment.

---

## 8. Architecture (one engine, two views)

```
Molecular pathology report (free text) + optional clinical context
        │
   Deployed app (public URL)
        │
   ENGINE (all the hard work — shared by both views):
     Claude: extract markers → WHO CNS5 classification
       │
     Live ClinicalTrials.gov API → candidate trials (glioma-wide)
       │
     Claude: per-criterion eligibility screen (met / not-met / unknown), negation-aware, cited
       │
     Verification agent: check every claim vs source; flag/rewrite overstatements
       │
     Postgres (app datastore: report, markers, trials, eligibility results)
        │
   ┌────┴───────────────────────┐
   ▼                            ▼
 CLINICIAN VIEW              PATIENT VIEW  (+1 plain-language step)
 eligibility screen,        same verified result in plain language,
 WHO class, citations,      what participation involves,
 verification log           questions to ask
```

- **LLM/agents**: Claude (extraction, classification, eligibility reasoning, verification, plain-language).
- **Data**: live ClinicalTrials.gov API; Postgres as the app datastore (hosted — Supabase/Neon).
- **Frontend**: single deployed app (Streamlit or Next.js), public URL.
- **Out of scope for MVP**: Neo4j, AACT bulk ingestion, RxNorm/ChEMBL, FDA PDF parsing. (Kept in the original PRD as the someday north star.)

### Build discipline
- **75/25**: clinician view is the hero (harder, higher-scoring, the user's intent); patient view is a lightweight second rendering. If the patient view starts eating the clinician view's time, cut it back to a stub.

---

## 9. Judging fit (Builder Track — Impact / Claude Use / Depth / Demo, 25% each)

- **Impact**: named clinician user + quantifiable time saved (N trials × M criteria screened in seconds vs hours); plus the patient handoff. Matches the official Builder example ("clinical trial matcher for a research coordinator… inclusion/exclusion reasoning shown for every match"), done deeply.
- **Claude Use**: per-criterion eligibility reasoning + negation handling + the **verification loop that catches its own overclaims** — well beyond a keyword-match baseline.
- **Depth**: 2021 WHO CNS5 integrated classification + structured eligibility with met/not-met/**unknown** + honest handling of missing data.
- **Demo**: paste a report → instant, cited eligibility screen, including a "looks eligible → correctly rejected by an exclusion" moment → one click to the patient-friendly view.

---

## 10. MVP scope (build during July 7–13)

- Population: glioma (main WHO CNS5 entities — IDH-wildtype glioblastoma, IDH-mutant astrocytoma, oligodendroglioma).
- One or two synthetic molecular reports across subtypes.
- WHO CNS5 classification from the report.
- Live ClinicalTrials.gov retrieval + per-criterion eligibility screen (met / not-met / unknown), negation-aware, cited.
- Three-agent verification loop.
- Deployed single-page app with a clinician view (hero) and a patient view (lightweight).

---

## 11. Product statement

**Glioma Copilot** turns a glioma molecular report into two things at once: for the clinician, an instant, source-grounded, per-criterion trial-eligibility screen that replaces hours of manual reading; for the patient, the same verified analysis in plain language for the conversation that follows. It classifies per the 2021 WHO standard, cites every claim, and verifies its own output to catch overstatements. It does not choose treatment, predict survival, or replace the clinician — it accelerates the team and closes the comprehension gap, on one grounded engine.
