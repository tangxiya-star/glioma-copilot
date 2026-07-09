# Glioma Evidence Review & Shared Decision Copilot — Demo Script

> **Built with Claude: Life Sciences** (Builder track). Core framing: doctors already
> know how to *find* glioma trials — the hard part is the **last mile after the list**:
> checking one patient against 20+ eligibility lines, catching what's still unknown,
> and deciding *with* the patient. That's what this copilot does — and every molecular
> fact is a **real, traceable de-identified TCGA sample**.

Live: frontend https://glioma-copilot.vercel.app/ · backend on Render (warm `/health`
before recording — free tier sleeps ~15 min).

---

## 0. The 20-second hook (say this first)

> "Finding glioma trials is largely solved — clinicians know what's recruiting, and
> tools like the National Brain Tumor Society's AI finder already match patients to a
> ranked list. The bottleneck is the review-and-decide work *after* the list: does
> *this* patient actually meet *all* the eligibility, what's still missing, and how do
> you and the patient decide together. Our copilot does that — over a **real** molecular
> profile, with every fit judgment cited and self-checked."

**Optional one-liner if a judge raises NBTS:** "The NBTS finder is actually Ancora.ai
white-labeled — a solid, dedicated matcher. But it's a *patient* tool: a 2-minute
questionnaire that helps someone *discover* trials and get *connected toward enrollment*.
We're a *clinician* tool for the opposite end — verifying, explaining, and documenting
whether a specific trial fits *this* patient's record. Their last mile is recruitment;
ours is clinical review." (See PRD §4.1.1.)

Why it wins: it's **Claude Use + Depth** in a place with real clinical stakes — not a
prettier trial search.

---

## 1. Setup (15s)

- Patient: **Case 001 — 64 y/o male, glioblastoma, IDH-wildtype** (real de-identified
  TCGA sample TCGA-06-6695).
- Say: "The **molecular data AND the prior treatment are both real, de-identified TCGA
  data** — molecular from cBioPortal, treatment (radiation + temozolomide) from the NIH
  GDC — for the same patient. Click the card and you land on that exact case. All four
  demo cases are patients recorded **alive**. Trials are **live from ClinicalTrials.gov**."
- Point at the green card: cBioPortal sample link + **GDC prior-therapy** link + marker chips.
- **Live-analysis proof (optional, strong):** in the sidebar "Load live case", type *any* real
  de-identified TCGA glioma barcode (or click a suggested one) → the app fetches that patient's
  molecular (cBioPortal) + treatment/clinical (GDC) **at request time** and runs the whole
  pipeline. Say: "Don't trust my preset cases — give me any real TCGA barcode and watch it
  classify and screen every trial live." (Survival is never fetched or shown.)

---

## 2. Report → deterministic WHO CNS5 classification (30s)

- Show the integrated neuropathology report (real molecular section + a clearly
  labeled *constructed clinical layer*).
- Click **Analyze**. The **WHO CNS5 classifier** returns *Glioblastoma, IDH-wildtype,
  grade 4* with **cited, step-by-step reasoning**.

> Talking point: "Claude normalizes the free-text report into fields; a **hardcoded
> rule engine** makes the actual diagnosis. Claude is **not** the source of truth — the
> classification is auditable and defensible."

---

## 3. Exhaustive candidate triage (40s)

Analyze also runs the candidate pipeline. Point at the counts as they land:

- **Stage 0 — pull *every* recruiting trial** for the tumor type (glioblastoma ≈ **326**),
  not a top-N slice.
- **Stage 1 — deterministic screen** flags hard conflicts (≈ 75 flagged / 251 clear),
  each with a **reason**, deprioritized but **never hidden**.
- **Stage 2 — real per-criterion fit** on the top screen-clear candidates, badged
  (✅ met · ❓ unknown · ❌ not-met) and sorted; header reads "deep-assessed N of 326."

> Talking point: "We consider **every** recruiting trial — so a good one buried at #50
> is never silently missed — then the expensive reasoning goes only where it matters.
> This is candidate *scoping for review*, not discovery; the clinician decides."

---

## 4. Per-criterion fit + the 3-agent verification (the money moment) (45s)

Open a trial → the **per-criterion table**: each eligibility line judged
met / not-met / unknown with the **exact line cited**.

Then click **Run 3-agent verification**:

- **Drafting agent**: "The patient is eligible for this trial."
- **Verification agent (Opus)**: catches it — a decisive criterion (EGFR) is **unknown**;
  **rewrites** to "potentially relevant; requires EGFR testing to confirm."
- **Investigation agent**: "Order EGFR amplification / EGFRvIII testing."

> Talking point: "The verification agent catches its **own** overclaim against the
> per-criterion evidence. That self-check is the difference between a demo and something
> a clinician would trust."

**Depth beat (switch to Case 004 if time):** a plain biomarker filter would say this
IDH-wildtype GBM patient "matches" recruiting GBM trials — but many **exclude prior
bevacizumab**, which lives in the clinical narrative, not a filter field. Our screen +
fit **catch the buried exclusion** and flag it `not-met`. That's the false-match a
filter can't see.

---

## 4.5 Evidence & sources — the third Claude surface (20s)

Under the fit table, expand **▸ Evidence & sources** — the trial's scientific
rationale, the patient's biomarkers, and the population prognosis, **each with a
clickable PMID → PubMed**.

> Talking point (this is the **Claude Use** beat — say it deliberately): "This uses
> **three Claude surfaces on purpose**: **Claude Code** built the app, the **Claude API**
> runs these review agents, and **Claude Science** generated this cited evidence layer.
> And we didn't trust it blindly — we verified **all 23 citations against PubMed: 23/23
> real, zero hallucinated**. That's the whole product's premise applied to our own
> pipeline: **Claude reasons, but never gets to be the source of truth.**"

Honesty note (if asked): the badge reads "PubMed-verified 23/23" because we actually ran
that check — not decoration. The layer is **traceability next to each claim, not an
explainer** — a clinician already knows why MGMT matters; the value is that every claim
is sourced.

---

## 5. Explain for the patient + shared decision (40s)

- Click **🗣 Explain for patient** → a plain-language card (~7th-grade). Note the
  honesty: unknowns become **"questions to confirm with your care team,"** never "you
  are eligible."
- Fill the **preference form** (entered doctor-guided, *not* in the chart): stay
  in-state (California), prefer to avoid Phase 1, prioritize quality of life.
- Click **Generate shared-decision summary**. The **preference-weighted ranking**
  visibly re-orders the assessed trials, and **every adjustment shows its reason**
  (e.g. "−25 · no site in California; out-of-state travel"). Plus a plain,
  non-directive **shared-decision note**.

> Talking point: "A biologically strong trial drops **because the patient told us she
> can't travel** — and you can see exactly why. That's shared decision-making, with the
> reasoning shown — not an algorithm overriding the patient."

---

## 6. Close (15s)

> "From a **real** molecular profile to a shared decision: classify with an auditable
> rule engine, consider **every** recruiting trial, verify against the **full**
> eligibility with citations, catch the overclaim, explain it plainly, and decide
> together — every fact traceable. Built across **three Claude surfaces** — Claude Code,
> the Claude API, and Claude Science — with the evidence **PubMed-verified**. **We don't
> pick the trial. We make the reasoning trustworthy.**"

---

## 7. If a judge pushes back — pre-loaded answers

- **"Isn't this just a trial matcher? Doctors already filter by IDH and get a pop-up list."** → Those tools do **discovery** — filter a few *structured* fields and return a list. We don't compete there; we take the candidate pool exhaustively and call it scoping, not matching. We fill the **last mile the clinician still does by hand after the list appears**: (1) check the *whole* record against the *whole* eligibility — 15–30 criteria, most of it free text a filter never reads — per criterion, cited; (2) surface what's **unknown/missing** as a next step; (3) **catch over-claims** (verify agent rewrites an over-stated "eligible" when a decisive criterion is actually unknown); (4) translate to plain language + a preference-aware shared-decision note. *Concrete:* a filter says our IDH-wildtype GBM patient "matches" recruiting GBM trials — but many **exclude prior bevacizumab**, which lives in the clinical narrative, not a filter field, so the match is **false**; our per-criterion fit catches it. From *"these trials may be relevant"* → *"why this one may or may not fit **this** patient, what's missing, and how you two decide."*
- **"Why an LLM? Age and KPS are fixed numbers — why not just if-statements / a rule engine?"** → Where it's cleanly structured we DO use deterministic code (our Stage-1 pre-screen — IDH, 1p/19q, prior-drug class — is pure `if`, no LLM). But a rule engine needs structured inputs on **both** sides, and neither is: trial eligibility is a free-text blob (KPS≥60 vs "ECOG 0-1" — a different scale — vs "able to care for self"; plus "adequate organ function", negation, "no prior bevacizumab **unless** >6 months"), and the patient's facts live in free-text EHR notes. Pre-LLM the blocker was never the comparison — it was *extracting* predicates from both texts, which is why trial matching is **still done by hand** today. The persistent manual workflow is the proof a rule engine doesn't scale. An LLM reads both free-text sides and judges per criterion **with citations**; we keep `if` for the clean slice (hybrid) and a verification agent to catch the LLM's own over-claims.
- **"Is this giving medical advice?"** → No. Non-goal by design. Language is "potentially relevant," "for clinician review." No survival prediction, no autonomous enrollment, no picking a trial.
- **"Is the molecular data real, or made up?"** → **Real**, de-identified, from two public sources: molecular from cBioPortal (`lgggbm_tcga_pub`, Cell 2016) and **prior treatment from the NIH GDC** — both for the same real TCGA case (all recorded **alive**). Case 004's prior **bevacizumab is a real GDC treatment record**, not invented. The only constructed bit is a small labeled overlay (Case 001's "EGFR not yet tested" gate). Click the green card's cBioPortal + GDC links to verify.
- **"Is the ranking a validated eligibility score?"** → No. It's a **transparent heuristic** re-weighting already-assessed trials by stated preferences; every adjustment shows its reason and delta. We deliberately avoid an unsupported "match %".
- **"Trial data goes stale."** → Trials are pulled **live** from ClinicalTrials.gov on each Analyze; every trial links to its NCT record.
- **"Did you cherry-pick a few trials?"** → No — we pull **all** recruiting trials for the tumor type and report "deep-assessed N of `<total>`"; screened-out trials stay listed and openable.
- **"You used Claude Science for the evidence — did you just trust what it generated?"** → No, and that's the point. Claude Science generated the cited evidence layer; we then **verified all 23 PMIDs against the PubMed E-utilities API — 23/23 real, 0 hallucinated** (3 epub/print years corrected to the PubMed canonical). It's the same principle the whole product runs on — **Claude reasons, but is never the source of truth** — applied to our own build pipeline. The badge "PubMed-verified 23/23" is a check we actually ran, not decoration.
- **"Isn't a 'why this biomarker matters' panel redundant — a neuro-oncologist already knows?"** → Correct, and it's not there to teach. It's **traceability**: every claim the app makes is sourced and clickable, so a skeptical clinician (or judge) can audit it in one click. The genuinely non-obvious content is the **per-trial rationale** and the **uncertainty flags**, not the settled facts.
- **"Could the verification agent over-flag — reject a patient who'd actually qualify?"** → That's the more costly error direction and we guard it explicitly. Verify is **symmetric-honest**: just as we never fake a catch (the drafter always sees the full fit assessment), verify may **never fake a doubt**. A downgrade must cite a specific `unknown`/`not_met` line from the fit table; a deterministic check reverts any flag that isn't grounded in a real line back to *supported* — it can't turn a `met` criterion into doubt. And regardless of what verify says, the **per-criterion table is always shown and flagged trials stay open**, so the clinician always sees the underlying evidence and decides. Softening the overall verdict to "confirm with the coordinator" is honest (final enrollment is never computable from registry text), but the doubt must be evidence-backed, not invented.

---

## Timing (target ~3-min video + live Q&A)

| Section | Time | Running |
|---------|------|---------|
| Hook | 0:20 | 0:20 |
| Setup + provenance | 0:15 | 0:35 |
| Report → classification | 0:30 | 1:05 |
| Exhaustive triage | 0:40 | 1:45 |
| Per-criterion fit + 3-agent verify | 0:45 | 2:30 |
| Evidence & sources (3rd Claude surface) | 0:20 | 2:50 |
| Explain + shared decision | 0:40 | 3:30 |
| Close | 0:15 | 3:45 |

Over 3:00 with everything in. To land a tight ~3-min cut, trim the Case-004 Depth beat
and shorten the shared-decision beat — but **keep the Evidence & sources beat**: the
"three Claude surfaces + PubMed-verified" line is your strongest **Claude Use** moment
and is worth the 20s. Keep the trimmed beats for live Q&A.
