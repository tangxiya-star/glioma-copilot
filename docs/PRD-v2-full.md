# Glioma Evidence Review & Shared Decision Copilot PRD

## 1. Product Name

**Glioma Evidence Review & Shared Decision Copilot**

> Scope: glioma-wide (2021 WHO CNS5) — IDH-wildtype glioblastoma, IDH-mutant astrocytoma, and oligodendroglioma. GBM is only a subset post-2021; the larger, more relevant population is glioma as a whole, which is also where recent therapeutic progress (e.g. IDH inhibitors in IDH-mutant glioma) is concentrated. GBM cases remain a natural flagship for demos.

> **Positioning note:** this is **not** a "clinical trial finder." At major academic centers (UCSF, Stanford, MD Anderson…) clinicians already know the relevant trials and coordinators handle recruitment/enrollment — discovery is not the pain. The value is helping clinicians **review, compare, verify, explain, and document** trial options for a specific patient. The goal is never "AI recommends Trial A"; it is "AI summarizes why Trial A may or may not be appropriate, for clinician review."

---

## 2. One-liner

An AI copilot that helps neuro-oncology teams **review and verify** the evidence behind candidate trials, **assess trial fit** for a specific patient (which eligibility criteria are met, what is still missing, which biomarkers matter, what logistical barriers and uncertainties remain), explain options in plain language, and capture patient preferences for shared decision-making in complex glioma care.

---

## 3. Context

Patients with glioma — spanning IDH-wildtype glioblastoma, IDH-mutant astrocytoma, and oligodendroglioma under the 2021 WHO CNS5 classification — often have limited standard options, making clinical trials an important part of care. The standard treatment backbone (surgery → chemoradiation → maintenance chemotherapy) is largely fixed and is *not* what this product tries to change.

Clinicians at academic centers usually already know which trials are recruiting, and coordinators handle enrollment. The hard, unmet work is everything *after* a trial is known: manually **reviewing and verifying** whether it actually fits *this* patient — reading long eligibility criteria, cross-checking molecular biomarkers (IDH, MGMT, EGFR, 1p/19q, CDKN2A/B…), prior treatments, and logistics — and judging what is satisfied, what is missing, and what is uncertain.

Trial fit is not only about medical eligibility. Clinicians also weigh patient age, performance status, prior treatments, geography, caregiver support, visit frequency, willingness to travel, and patient goals — and these preferences are rarely captured in a structured way.

This review-and-verify process is time-consuming, difficult to keep source-grounded, and hard to document transparently during clinical decision-making.

---

## 4. Problem

The bottleneck is **not** finding trials (clinicians and coordinators largely know what is recruiting). It is the review-and-decision work that follows, which today is fragmented:

- Evidence for a known trial's fit is scattered across ClinicalTrials.gov, papers, FDA documents, and internal knowledge.
- Trial eligibility criteria are written in long, complex language, and checking a specific patient against them by hand is slow and error-prone.
- Claims (eligibility met, biomarker matches, regulatory facts) are hard to verify at the point of decision.
- Patient preferences are often discussed verbally but not captured in a structured way.
- Doctors must translate complex trial language into understandable explanations during emotionally difficult conversations.

This creates a gap between:

1. Evidence review & trial fit assessment  
2. Patient communication  
3. Shared decision documentation  

---

## 5. Target Users

### Primary User: Neuro-oncologist / Oncology Clinician

Needs to quickly review relevant trials and evidence before discussing options with a patient.

### Secondary User: Patient + Caregiver

Needs to understand trial options in plain language and express preferences around travel, risk tolerance, quality of life, caregiver support, and logistics.

### Supporting User: Clinical Trial Coordinator

May help screen eligibility, confirm trial availability, and follow up with trial sites.

---

## 6. Core Use Case

A patient with glioma (e.g. recurrent GBM, or IDH-mutant astrocytoma) is being seen by a neuro-oncology team. The clinician already has a few candidate trials in mind and wants to **review and verify why each may or may not fit** this patient, explain the options clearly, and document the patient’s preferences and next steps — not to have software discover or pick a trial.

---

## 7. Product Goals

1. Turn "we know this trial" into a fast, verifiable, patient-specific **fit assessment** (criteria met / missing / uncertain).
2. Make trial options understandable to patients via clinician-led plain-language explanation.
3. Capture patient preferences in a structured way and integrate them into the discussion (a real-world differentiator).
4. Support shared decision-making without replacing clinical judgment.
5. Ensure every claim is source-grounded and verifiable, and produce a transparent shared-decision summary.

---

## 8. Non-Goals

This product does **not**:

- Recommend a treatment independently.
- Replace clinician judgment.
- Predict survival.
- Give direct medical advice to patients.
- Automatically enroll patients in trials.
- Classify free-text clinical rationale into unsupported scoring systems.

---

## 9. Product Positioning

This is not a treatment recommendation tool.

It is a **verified evidence and shared decision support layer** for complex neuro-oncology care.

The goal is to help clinicians and patients understand the evidence together, surface real-world constraints, and document the reasoning behind trial discussions.

### Positioning sentence

> We do not help AI choose a clinical trial. We help clinicians and patients understand the evidence together, surface patient preferences, and document shared decision-making.

---

# 10. User Workflow

**Overall flow (clinician-driven, in order):**

```
Patient Case
   ↓
Evidence Review
   ↓
Trial Fit Assessment
   ↓
Evidence Verification
   ↓
Plain-language Explanation
   ↓
Patient Preference Capture
   ↓
Shared Decision Summary
```

(Contrast with the rejected framing: Patient → Find Matching Trials → Patient Chooses. The clinician reviews evidence first; the patient never independently evaluates eligibility or picks a trial.)

## Step 1: Clinician Workspace

The clinician uploads or enters patient context:

- Diagnosis: Glioma (glioblastoma / astrocytoma / oligodendroglioma per 2021 WHO CNS5)
- Disease state: newly diagnosed / recurrent
- Age
- Location
- Prior treatments
- Molecular markers: IDH, MGMT, EGFR, 1p/19q, CDKN2A/B, TERT
- Performance status if available
- Travel constraints if known
- The candidate trials the clinician is considering

For those candidate trials, the system reviews and assembles:

- Trial status
- Eligibility criteria
- Related drugs
- Biomarker requirements
- Regulatory history where available
- Evidence conflicts or uncertainties

Output:

- Evidence brief per trial
- **Trial Fit Assessment**: eligibility criteria met / missing / uncertain
- Source citations
- Verification warnings

---

## Step 2: Shared Decision Workspace (doctor-guided)

This is **not** a place where patients search for or evaluate trials themselves. It is used by the clinician and patient together, in this order:

```
Clinician reviews evidence first
        ↓
Clinician explains options using AI-generated plain language
        ↓
Patient expresses preferences
        ↓
System generates a shared decision summary
```

For each trial, the system shows:

### Clinician View

- Trial name
- Phase
- Location
- Eligibility rationale
- Required biomarker match
- Prior treatment requirements
- Visit frequency
- Evidence summary
- Risks / uncertainty
- Source links

### Patient-Friendly View

Plain-language explanation of:

- What the trial is testing
- Why the patient may qualify
- What participation may involve
- Travel or visit burden
- What is known and unknown
- Questions to ask the care team

Example:

> This study is testing an experimental treatment for patients whose tumors have a certain molecular marker. Your pathology report suggests you may match that marker. The trial may require regular visits and additional scans. It is not guaranteed to help, but it may provide access to a treatment not otherwise available.

---

## Step 3: Patient Preference Capture

The patient or caregiver can answer structured questions:

- Are you willing to travel out of state?
- How often can you come to the hospital?
- Is quality of life or aggressive treatment the higher priority right now?
- Are you open to early-phase experimental trials?
- Do you have caregiver support?
- Are cost, lodging, or insurance concerns important?
- Would you consider another biopsy if required?

These preferences are not used to make final decisions, but to help clinicians understand realistic trial fit.

---

## Step 4: Discussion Summary

The system generates a shared decision summary:

- Trials discussed
- Why each trial may fit
- Why each may not fit
- Patient preferences expressed
- Open questions
- Next steps

Example:

> The patient prefers to remain within California if possible and is concerned about weekly travel. Trial A appears medically relevant but requires out-of-state visits. Trial B is closer and may be easier logistically, but eligibility needs confirmation with the trial coordinator.

---

# 11. Key Features

## 11.1 Patient Case Intake

- Structured form for diagnosis, markers, treatments, location, and preferences.
- Optional mock patient upload for demo.

## 11.2 Evidence Graph

Stores connected data for:

- Trials
- Drugs
- Biomarkers
- Sponsors
- Locations
- Regulatory records
- Trial statuses

## 11.3 Trial Fit Assessment

For each candidate trial under clinician review, the system does **not** rank-to-recommend; it assesses *fit* and surfaces the reasoning for clinician review. It answers:

- Why is this trial potentially relevant?
- Which eligibility criteria are already satisfied?
- Which information is still missing?
- What biomarkers matter?
- What are the logistical barriers (travel, visit frequency)?
- What uncertainties remain?

Assessed against: disease/entity (2021 WHO), recurrence status, biomarkers, prior treatments, age, location/logistics, trial status, and patient preferences. Output framing is always "why Trial A may or may not be appropriate," never "Trial A is recommended."

## 11.4 Evidence Verification

Three-agent workflow:

### Drafting Agent

Creates a source-grounded evidence brief.

### Verification Agent

Checks each claim against structured records and flags unsupported or ambiguous claims.

### Investigation Agent

Queries additional records or narrows unsupported claims.

## 11.5 Plain-Language Explanation

Translates clinician-facing trial language into patient-friendly explanations.

## 11.6 Preference-Aware Trial Review (key differentiator)

Integrates patient preferences into the trial discussion — annotating fit based on preferences that are rarely captured by existing trial-review tools but are decisive in real-world decisions:

- Willingness to travel
- Quality of life vs. aggressive treatment
- Family / caregiver support
- Visit burden
- Interest in experimental therapies
- Financial or lodging concerns

Preferences shape and document the discussion; they do not make the decision or let the patient pick a trial.

## 11.7 Shared Decision Note

Generates a clinician-reviewed summary suitable for documentation.

---

# 12. Data Sources

## 12.1 Clinical Trial Data

**Source:** ClinicalTrials.gov API / AACT  
**Use for:** trial title, status, phase, location, sponsor, eligibility criteria, intervention, condition.

ClinicalTrials.gov provides official study records. AACT provides a structured database version of ClinicalTrials.gov with tables for conditions, interventions, sponsors, facilities, and MeSH-linked browse terms.

### Fields needed

```text
NCT ID
Trial title
Condition
Intervention
Phase
Recruitment status
Eligibility criteria
Age range
Sex
Locations / facilities
Sponsor
Study start / completion dates
```

### Example query scope

```text
condition = glioblastoma OR glioblastoma multiforme
study_type = interventional
intervention_type = drug / biological / device
status = recruiting OR active not recruiting OR completed
```

---

## 12.2 Drug Normalization Data

**Source:** RxNorm + ChEMBL  
**Use for:** mapping messy drug names to canonical drug names.

RxNorm can help match brand names, generic names, drug products, and ingredients to RxCUI identifiers. ChEMBL can provide drug and molecule metadata, including synonyms and drug indications.

### Fields needed

```text
Drug name
Brand name
Generic name
Synonyms
RxCUI
ChEMBL ID
Ingredient
Drug class
```

### Example mapping

```text
Temodar
TMZ
Temozolomide 150mg capsule
        ↓
Canonical Drug: Temozolomide
```

---

## 12.3 Regulatory Evidence

**Source:** FDA Drugs@FDA / openFDA labels / FDA approval packages  
**Use for:** FDA label, indication, approval status, regulatory history.

### Fields needed

```text
Drug
FDA label
Indication
Approval date
Approval package URL
Regulatory body
Outcome
Narrative text
```

---

## 12.4 Biomarker / Molecular Data

**Source:** extracted from trial eligibility + mock patient pathology report  
**Use for:** matching trial criteria to GBM molecular profile.

For hackathon MVP, we can manually normalize a small biomarker dictionary:

```text
IDH wildtype
IDH mutant
MGMT methylated
MGMT unmethylated
EGFR amplification
TERT mutation
1p/19q codeletion
```

### Where found

```text
Trial eligibility criteria
Pathology report
Molecular testing report
Mock patient case
```

---

## 12.5 Patient Case Data

For demo, use either:

```text
Option A: Synthetic mock GBM patient
Option B: Public de-identified GBM dataset
Option C: Manually created case based on public trial eligibility patterns
```

For a hackathon, the safest MVP is a **synthetic mock patient** to avoid privacy issues.

### Fields needed

```text
Age
Diagnosis
Disease state: newly diagnosed / recurrent
Location
Prior treatments
Molecular markers
Performance status
Travel preference
Caregiver support
Treatment goals
```

---

# 13. Tech Stack

## 13.1 Frontend

```text
Next.js / React
Tailwind CSS
shadcn/ui
Framer Motion optional
```

Use for:

```text
Clinician workspace
Shared decision workspace
Patient preference form
Trial cards
Evidence citations
```

---

## 13.2 Backend

```text
FastAPI
Python
Pydantic
```

Use for:

```text
API endpoints
Trial retrieval
Evidence bundle construction
Agent orchestration
```

---

## 13.3 Database

```text
PostgreSQL (Neon, hosted)
psycopg (v3)
```

Use for:

```text
Drug → Trial
Trial → Sponsor
Trial → Location
Trial → Biomarker
Drug → FDA Record
Patient → Preference
Patient → Candidate Trial
```

> **Decision (Jul 7):** relationships are modeled in **Postgres**, not Neo4j.
> The data set is small and these relationships express cleanly as tables +
> join tables + foreign keys; Neo4j + Cypher would add setup and modeling
> overhead not worth it inside the hackathon window. Neo4j is deferred to a
> post-hackathon "graph" iteration (see §13.6).

---

## 13.4 LLM / Agents

```text
Claude API
```

Use for:

```text
Drafting Agent
Verification Agent
Investigation Agent
Plain-language Explanation Agent
Shared Decision Summary Agent
```

Important framing:

```text
Claude is not the source of truth.
Claude only reasons over retrieved source records.
```

---

## 13.5 Data Processing

```text
Python
pandas
requests
BeautifulSoup if needed
pdfplumber / PyMuPDF for PDFs
```

Use for:

```text
ClinicalTrials.gov ingestion
Drug name normalization
FDA PDF parsing
Eligibility text extraction
```

---

## 13.6 Deferred / post-hackathon

```text
Neo4j + Cypher (graph relationships)
```

Considered as the primary store but **deferred**: for the MVP the same
drug / trial / biomarker / sponsor / location relationships live in Postgres
(§13.3). Revisit Neo4j only if relationship queries outgrow SQL joins.

---

# 14. High-Level Architecture

```text
                    ┌─────────────────────────┐
                    │   ClinicalTrials.gov    │
                    │       / AACT            │
                    └───────────┬─────────────┘
                                │
                    ┌───────────▼─────────────┐
                    │   Trial Ingestion        │
                    │   + Eligibility Parser   │
                    └───────────┬─────────────┘
                                │
┌──────────────┐     ┌──────────▼──────────┐      ┌──────────────┐
│ RxNorm       │────▶│ Canonical Drug       │◀──── │ ChEMBL       │
│ ChEMBL       │     │ Resolution Layer     │      │ Drug Data    │
└──────────────┘     └──────────┬──────────┘      └──────────────┘
                                │
                    ┌───────────▼────────────┐
                    │        Neo4j Graph      │
                    │ Drug-Trial-Biomarker    │
                    │ FDA-Location-Sponsor    │
                    └───────────┬────────────┘
                                │
                    ┌───────────▼────────────┐
                    │      FastAPI Backend    │
                    └───────────┬────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
 Drafting Agent          Verification Agent       Explanation Agent
        │                       │                       │
        └───────────────┬───────┴───────────────┬───────┘
                        ▼                       ▼
              Clinician Workspace      Shared Decision Workspace
```

---

# 15. UI Frames

## Frame 1: Clinician Workspace

```text
┌──────────────────────────────────────────────────────────────────────┐
│ GBM Trial Evidence Copilot                                           │
├──────────────────────────────────────────────────────────────────────┤
│ Patient: Mock Case 001                         Status: Recurrent GBM │
│ Age: 58                                        Location: California  │
│ IDH: Wildtype                                  MGMT: Methylated      │
│ Prior Tx: Surgery + Radiation + Temozolomide                         │
└──────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────┬──────────────────────────────────────┐
│ Patient Summary               │ Evidence Alerts                      │
├───────────────────────────────┼──────────────────────────────────────┤
│ Diagnosis: GBM                │ ⚠ Trial A requires out-of-state travel│
│ Disease State: First recurrence│ ⚠ Trial B requires EGFR alteration   │
│ Performance: ECOG 1           │ ✓ MGMT status found in pathology     │
│ Travel: Prefers in-state      │ ? EGFR status not found              │
└───────────────────────────────┴──────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│ Candidate Trials                                                     │
├─────┬──────────────────────┬───────────┬────────────┬───────────────┤
│ Fit │ Trial                │ Phase     │ Location   │ Why Matched   │
├─────┼──────────────────────┼───────────┼────────────┼───────────────┤
│ 92% │ Trial A              │ Phase II  │ UCSF       │ GBM + MGMT    │
│ 76% │ Trial B              │ Phase I   │ Stanford   │ Recurrent GBM │
│ 41% │ Trial C              │ Phase I/II│ Boston     │ Travel issue  │
└─────┴──────────────────────┴───────────┴────────────┴───────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│ Selected Trial Evidence Brief                                        │
├──────────────────────────────────────────────────────────────────────┤
│ Trial A is recruiting patients with recurrent glioblastoma. [NCT...] │
│ The trial includes patients with prior radiation therapy. [NCT...]   │
│ MGMT methylation is relevant to this patient’s profile. [Pathology]  │
│                                                                      │
│ Verification Status:                                                 │
│ ✓ Trial status supported                                             │
│ ✓ Location supported                                                 │
│ ⚠ EGFR status not available in current patient record                │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Frame 2: Trial Detail / Evidence Verification

```text
┌──────────────────────────────────────────────────────────────────────┐
│ Trial Detail: Trial A                                                │
├──────────────────────────────────────────────────────────────────────┤
│ Phase: II                                                            │
│ Status: Recruiting                                                   │
│ Location: UCSF Medical Center                                        │
│ Sponsor: Example Biotech                                             │
│ Intervention: Drug X                                                 │
└──────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────┬──────────────────────────────────────┐
│ Eligibility Match             │ Source Evidence                      │
├───────────────────────────────┼──────────────────────────────────────┤
│ ✓ Recurrent GBM               │ ClinicalTrials.gov condition field   │
│ ✓ Age 18+                     │ Eligibility criteria                 │
│ ✓ Prior radiation allowed     │ Eligibility criteria                 │
│ ? EGFR status needed          │ Eligibility criteria mentions EGFR   │
│ ⚠ Travel burden               │ Trial site outside preferred radius  │
└───────────────────────────────┴──────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│ Verification Agent Log                                               │
├──────────────────────────────────────────────────────────────────────┤
│ Claim: "Patient is eligible for Trial A."                            │
│ Status: Ambiguous                                                    │
│ Reason: Patient matches disease and age, but EGFR status is unknown. │
│ Resolution: Reworded as "Potentially relevant; needs EGFR check."    │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Frame 3: Shared Decision Workspace

```text
┌──────────────────────────────────────────────────────────────────────┐
│ Shared Decision Workspace                                            │
│ For clinician + patient conversation                                 │
└──────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────┬──────────────────────────────────────┐
│ Clinician View                │ Patient-Friendly Explanation         │
├───────────────────────────────┼──────────────────────────────────────┤
│ Trial A                       │ This study is testing a new treatment│
│ Phase II                      │ for glioblastoma that has come back. │
│ Recruiting                    │ Based on your current records, you   │
│ Requires recurrent GBM        │ may be a possible match, but one lab │
│ Requires EGFR result          │ result still needs to be checked.    │
│ UCSF site                     │                                      │
│                               │ What participation may involve:      │
│ Evidence:                     │ • Regular visits to UCSF             │
│ [NCT...] [Pathology...]       │ • MRI scans                          │
│                               │ • Possible extra testing             │
└───────────────────────────────┴──────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│ Patient Preferences                                                  │
├──────────────────────────────────────────────────────────────────────┤
│ Treatment goal:      [ Balance survival and quality of life     ▼ ]  │
│ Travel preference:   [ California only                         ▼ ]  │
│ Visit frequency:     [ Up to every 2 weeks                     ▼ ]  │
│ Experimental trial:  [ Open to Phase II, unsure about Phase I   ▼ ]  │
│ Caregiver support:   [ Available 2 days per week                ▼ ]  │
│ Biggest concern:     [ Travel burden + side effects             ▼ ]  │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Frame 4: Preference-Aware Trial Comparison

```text
┌──────────────────────────────────────────────────────────────────────┐
│ Trial Fit After Patient Preferences                                  │
├─────┬────────────┬──────────────┬──────────────┬────────────────────┤
│ Rank│ Trial      │ Medical Fit  │ Preference Fit│ Reason             │
├─────┼────────────┼──────────────┼──────────────┼────────────────────┤
│ 1   │ Trial A    │ High         │ High          │ In-state + Phase II │
│ 2   │ Trial B    │ Medium       │ Medium        │ Local but Phase I   │
│ 3   │ Trial C    │ High         │ Low           │ Requires Boston     │
└─────┴────────────┴──────────────┴──────────────┴────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│ Why Trial C moved down                                               │
├──────────────────────────────────────────────────────────────────────┤
│ Trial C appears medically relevant, but it requires travel to Boston.│
│ The patient stated a preference to remain within California.         │
│ This trial may still be worth discussing if travel support is found. │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Frame 5: Shared Decision Summary

```text
┌──────────────────────────────────────────────────────────────────────┐
│ Shared Decision Summary                                              │
├──────────────────────────────────────────────────────────────────────┤
│ Discussed Options:                                                   │
│ • Trial A: medically relevant and located in California              │
│ • Trial B: local, but earlier-stage and more experimental            │
│ • Trial C: medically relevant but requires out-of-state travel       │
│                                                                      │
│ Patient Preferences:                                                 │
│ • Prefers to remain in California                                    │
│ • Values quality of life and fewer hospital visits                   │
│ • Open to clinical trials but unsure about Phase I studies           │
│                                                                      │
│ Open Questions:                                                      │
│ • Confirm EGFR status                                                │
│ • Contact Trial A coordinator about visit schedule                   │
│ • Ask whether travel support exists for Trial C                      │
│                                                                      │
│ Suggested Note Draft:                                                │
│ Patient and clinician reviewed clinical trial options. Patient       │
│ expressed preference for in-state trials and concern about frequent  │
│ travel. Trial A will be explored further pending biomarker review.   │
└──────────────────────────────────────────────────────────────────────┘
```

---

# 16. Example Demo Scenario

Patient:

- 58-year-old recurrent GBM patient
- IDH-wildtype
- MGMT methylated
- Prior surgery, radiation, temozolomide
- Lives in California
- Prefers not to travel out of state
- Values quality of life and fewer hospital visits

System output:

- Finds relevant recruiting GBM trials.
- Filters or annotates based on molecular markers.
- Flags out-of-state trials as logistically difficult.
- Generates clinician evidence brief.
- Generates plain-language explanation for patient.
- Captures patient preference.
- Produces shared decision summary.

---

# 17. Success Metrics

For prototype:

- Can retrieve relevant trials for a mock GBM case.
- Can explain why a trial may match or not match.
- Every clinical claim links to a source.
- Verification agent catches at least one unsupported or ambiguous claim.
- Patient preference changes the trial discussion output.
- Final output includes both clinician-facing and patient-facing language.

---

# 18. Risks

## 18.1 Clinical Risk

The product could be misinterpreted as making medical recommendations.

### Mitigation

Use language such as:

- “evidence for clinician review”
- “discussion support”
- “potentially relevant trial”
- not “recommended treatment”

---

## 18.2 Evidence Risk

Trial data may be stale or incomplete.

### Mitigation

Show source, last updated date, and uncertainty state.

---

## 18.3 Patient Communication Risk

Plain-language explanations may oversimplify uncertainty.

### Mitigation

Always include:

- what is known
- what is unknown
- questions to ask your doctor

---

# 19. MVP Scope

For hackathon:

- Population: glioma (2021 WHO CNS5); a GBM case as the flagship demo
- One or two mock patient cases (molecular report + context)
- Live ClinicalTrials.gov retrieval for the candidate trials under review
- **Trial Fit Assessment** per trial (criteria met / missing / uncertain), source-cited
- Lightweight datastore (Postgres — not Neo4j/AACT for the MVP)
- Three-agent verification loop (drafting / verification / investigation)
- Two interfaces:
  - Clinician evidence workspace (primary)
  - Doctor-guided shared decision workspace (differentiator: plain-language explanation → preference capture → shared decision summary)

---

# 20. MVP Build Plan

## Day 1

```text
Build mock patient case
Pull 20–50 GBM trials from ClinicalTrials.gov
Create simple trial table
```

## Day 2

```text
Normalize drug names using RxNorm / manual dictionary
Extract biomarkers from eligibility text
Load graph into Neo4j or PostgreSQL
```

## Day 3

```text
Build Clinician Workspace UI
Build trial cards
Add source citations
```

## Day 4

```text
Implement Claude agents:
Drafting Agent
Verification Agent
Investigation Agent
Plain-language Agent
```

## Day 5

```text
Build Shared Decision Workspace
Add patient preference form
Generate shared decision summary
Polish demo story
```

---

# 21. Demo Story

```text
A 58-year-old recurrent GBM patient has already received surgery,
radiation, and temozolomide.

The clinician needs to discuss clinical trial options, but trial data is
fragmented across ClinicalTrials.gov, eligibility criteria, biomarker
reports, and regulatory evidence.

Our system helps the clinician identify relevant trials, verify why they
may fit, translate trial language into patient-friendly explanations, and
capture patient preferences such as travel limits and quality-of-life goals.

The final output is not a treatment recommendation. It is a verified,
source-grounded shared decision brief for clinician review.
```

---

# 22. Future Expansion

- Integrate EHR notes directly.
- Add trial coordinator workflow.
- Support multiple cancers.
- Add patient portal integration.
- Track trial status changes over time.
- Add multilingual patient explanations.
- Add insurance and travel support resources.
- Generate documentation back into the clinical note.
- Add follow-up reminders for trial coordinator outreach.
- Add patient-facing education packets.
- Add palliative care and goals-of-care discussion support where clinically appropriate.

---

# 23. Final Product Statement

**Glioma Evidence Review & Shared Decision Copilot** helps neuro-oncology teams synthesize patient-specific evidence, assess whether each trial actually fits, verify every claim against its source, explain the options in plain language, capture what matters to the patient, and generate a transparent shared-decision summary — with the clinician in control at every step.

It does not find trials for you, recommend one, choose treatment, predict survival, or replace clinician judgment.

It makes the reasoning behind a trial discussion fast, verifiable, and documented — helping clinicians and patients understand complex trial options together.
