# CLAUDE.md — project context & handoff

> Auto-loaded when Claude Code starts in this repo. Read this first, then `docs/PRD-v2-full.md`. This is a **hackathon project handoff** — it captures decisions and *why*, so a fresh session can continue without re-litigating.

---

## What this is

A hackathon project: **Glioma Evidence Review & Shared Decision Copilot** — an AI copilot that helps neuro-oncology clinicians **review, verify, assess-fit, explain, and document** clinical-trial options for a specific glioma patient. **It is NOT a "trial finder."**

Canonical PRD: **`docs/PRD-v2-full.md`**. Everything below is the condensed rationale.

This repo is the **code repo** (build during the hackathon). The planning/thinking docs live in `docs/`.

---

## Hackathon context (important constraints)

- **Event**: Built with Claude: Life Sciences (Cerebral Valley × Anthropic × Gladstone Institutes). Remote/virtual.
- **Timeline**: hacking **July 7 → July 13, 9:00 PM ET (submission deadline)**. Judging July 14–15 (async) + July 16 live final.
- **Track**: **Builder Track**. Uses **Claude Code** (build) + **Claude API** (in-app agents). NOT "Claude Science" (that's the Researcher track).
- **Team size**: up to 2.
- **Judging (4 × 25%)**: Impact / **Claude Use** (creative, beyond basic) / Depth & Execution / Demo.
- **HARD RULES**:
  - **Open source** — everything shown must be under an approved OSS license. (Repo currently private for dev; **make public before submission**.)
  - **New work only** — all *code* must be built during July 7–13. Planning docs (in `docs/`) are prior thinking and allowed; **pre-writing code or pre-ingesting data is NOT**. Commits are dated in-window.
- **Deliverables**: 3-min demo video + open-source repo + 100–200 word summary.
- **Official Builder example** (near-verbatim our idea): *"A clinical trial matcher for a research coordinator — takes free-text patient notes and surfaces eligible trials from ClinicalTrials.gov, with the inclusion/exclusion reasoning shown for every match."* We do a deeper version.

---

## Key product decisions (and why) — do not re-litigate

1. **Not a trial finder.** Domain experts said clinicians already know the trials; coordinators handle recruitment. Discovery is not the pain. Value = **review / verify / assess-fit / explain / document**. Goal is never "AI recommends Trial A" — it's "AI summarizes why Trial A may or may not be appropriate, for clinician review."
2. **Scope = whole glioma, not just GBM.** Post-2021 WHO CNS5, GBM is a subset (IDH-wildtype); IDH-mutant tumors are astrocytoma with longer survival. Glioma is the larger population and where recent progress is (e.g. IDH inhibitors). GBM = flagship demo case.
3. **Treatment is fixed** (surgery → chemoradiation → maintenance). No treatment decision support.
4. **"Trial Matching" → "Trial Fit Assessment."** Per trial: why relevant? criteria met? what's missing? which biomarkers? logistical barriers? uncertainties?
5. **Patient side is doctor-guided, not patient self-search.** Flow: clinician reviews → clinician explains with AI plain-language → patient expresses preferences → system generates shared decision summary.
6. **Patient preferences = a key differentiator** (travel, QoL vs aggressive, caregiver support, visit burden, experimental-therapy interest, financial/lodging).
7. **Three-agent architecture** (Drafting → Verification → Investigation). Evidence reasoning, not autonomous decisions. **Claude is not the source of truth; it only reasons over retrieved records.**
8. **Red lines**: no discovery-as-hero, no autonomous recommendation, no treatment recommendation, **no individual survival prediction** (prognosis only as sourced population ranges + uncertainty), no autonomous enrollment, does not replace clinician judgment.

---

## Tech decisions for the MVP build

- **Data**: **live ClinicalTrials.gov v2 API** (real, full corpus, no key). Not AACT bulk ingestion.
- **Store**: **Neon Postgres** as the app datastore (hosted). Not Neo4j.
- **Drug-name normalization** *(✅ DONE — both tiers built)*: `backend/app/drugs.py`. **Claude names** the drug mention → **Tier 1 RxNorm/RxNav** (key-free) resolves RxCUI + canonical ingredient (exact then approximate match; Temodar/TMZ → temozolomide) → **Tier 2 ChEMBL** adds mechanism of action / class (bevacizumab → "VEGF-A inhibitor" = grounds "prior anti-VEGF"). Cached in Postgres (`drug_normalizations`). Endpoints `POST /api/drugs/normalize` + `/api/drugs/from_patient`; UI card after Analyze with RxCUI/ChEMBL links. Reinforces "Claude is not the source of truth." PRD §12.2 documents it. (Next step, not done: feed ChEMBL mechanism into the Stage-1 pre-screen for drug-class matching.)
- **Regulatory**: openFDA JSON API is an optional groundedness add. **No FDA PDF parsing.**
- **Agents**: Claude API — extraction, WHO CNS5 classification, drafting, verification, investigation, plain-language.
- **Frontend / stack** *(decided Jul 7)*: **Next.js (React + Tailwind + shadcn/ui) → Vercel**, **FastAPI backend → Render/Railway/Fly**, **Neon Postgres**. (Builder knows frontend, so the PRD's real stack, not the Streamlit fallback.) Builder track requires shippable "software they could use without you in the room."
- **Out of scope for MVP** (someday north-star only): Neo4j, AACT, FDA PDF parsing. *(RxNorm/ChEMBL moved in-scope as Tier 1/2 — see drug-name line.)*
- **Depth goes into the reasoning/verification layer** (visible in a 3-min demo; scores on Claude Use + Depth + Demo), NOT into invisible data plumbing.

---

## File map

| File | What it is |
|------|-----------|
| **`docs/PRD-v2-full.md`** | **Canonical PRD** — full current direction. Start here. |
| **`docs/six-day-build.md`** | **The execution plan for July 7–13** — day-by-day, stack locked, cut-line. Follow this to build. |
| `docs/demo_script.md` | Pitch script + pre-loaded Q&A. |
| `docs/demo_data_pack.md` | Real trials aligned to a synthetic GBM case; rehearsal/fallback. |

> Superseded planning docs (PRD-v1-lean, PRD-中文版, one-day-demo, five-day-build) were removed on Jul 7 to reduce confusion — all recoverable from git history. Regenerate a synced Chinese PRD on demand if the family reviewer needs one.

---

## Current status & next steps  (updated mid-build — Day 0→4 done)

**Stack (built):** Next.js (frontend/ → Vercel) + FastAPI (backend/ → Render) + Neon
Postgres + Claude API. Per-agent model config (`backend/app/config.py` AGENT_MODELS:
verify→Opus 4.8, rest→Sonnet 5) and per-agent effort (AGENT_EFFORT; fit→low for fast
streaming, verify→high). Deployed:
- Frontend: https://glioma-copilot.vercel.app/
- Backend:  https://glioma-copilot-api.onrender.com  (free tier sleeps ~15min → first hit ~30-50s; warm it before demos)
- Secrets live in local `.env` (gitignored) and each host's dashboard env vars.

**Done (Day 0→4):**
- Day 0: scaffold + Neon + Claude verified; deployed both ends.
- Day 1: live ClinicalTrials.gov v2 fetch (`backend/app/trials.py`); synthetic patients (`patient.py`); marker extraction (`POST /api/extract`).
- Day 2: **deterministic** WHO CNS5 classifier (`classify.py`) — Claude normalizes report → profile, hardcoded rules decide diagnosis (grounds "Claude is not the source of truth"); Postgres schema (`schema.sql`: patients/trials/eligibility_results) + storage.
- Day 3: per-criterion Trial Fit Assessment (`POST /api/fit` + `/api/fit/stream`, NDJSON streamed one criterion at a time); met/not_met/unknown + citations + negation; patient-matched trial retrieval (condition derived from diagnosis).
- Day 4: three-agent loop (`POST /api/review/stream`): draft → verify (Opus, grounds/rewrites overclaims) → investigate. Clinician-view log in UI.
- 4 synthetic demo cases (`patient.py`): 001 GBM IDH-wt (EGFR **unknown** → verify-catch scenario), 002 astrocytoma IDH-mut g4, 003 oligodendroglioma, 004 recurrent GBM with **prior bevacizumab** (genuine buried exclusion vs NCT05432804 → reliable "looks eligible → correctly flagged" Depth demo).

**Key honest findings (do not regress):**
- **not_met** conflicts (e.g. bevacizumab) → the system reliably & correctly rejects; draft concludes "not eligible" itself, so verify has nothing to override. This is the reliable Depth demo (Case 004).
- **unknown** gates (e.g. EGFR untested) → the only honest scenario where "verify catches an overstated 'eligible'". A strong drafter (Sonnet 5) often hedges correctly, so the catch is NOT guaranteed. The honest lever to make it reliable is a genuinely weaker drafter (Haiku) — NOT withholding the fit results from the draft (that's mock/rigging, explicitly rejected by the user). Draft currently sees the full fit assessment.

**UX/credibility refactor BEFORE Day 5 — ✅ ALL 5 DONE (+ case-speed fix).**

All five tasks below are implemented, verified, and committed on `main`:
- (1) **Proactive fit triage** — `POST /api/triage/stream` runs real per-criterion
  fit across the top N (cap 5) matched candidates after Analyze, badges each
  (✅/❓/❌ + signal looks_eligible/needs_workup/conflict), sorts by fit; full
  items cached client-side for instant drill-down + 3-agent reuse.
- (2) **Flow order** — trials gated behind Analyze (no mount-time broad fetch);
  case-switch clears trials/fit/triage and prompts "Analyze first".
- (3) **Real pathology-report format** — `patient.py` reports rebuilt as an
  integrated neuropathology report (patient/specimen, clinical history,
  microscopic, named IHC clones + assay platforms, WHO CNS5 integrated dx, demo
  sign-out) via a `_report()` builder.
- (4) **Real molecular provenance** — each case maps to a real de-identified TCGA
  sample (cBioPortal `lgggbm_tcga_pub`, Cell 2016, PMID 26824661); real curated
  markers + real variant calls; `/api/patients` returns `provenance`; UI shows a
  "Real molecular data · de-identified" card + clickable cBioPortal link. See
  memory `glioma-case-provenance` for the case→sample map.
- (5) **Preferences out of the chart** — preference wording stripped from reports
  (belongs in the Day-5 form).
- (+) **Case-speed fix** — `/api/patients` returns reports inline; case-switch is
  now pure in-memory (no per-switch fetch).
- Verified: all 4 cases still classify to their intended WHO CNS5 diagnosis on
  the new real-data reports. REAL molecular vs CONSTRUCTED clinical layer is
  labeled in every report (honesty).

**Superseded task detail (kept for rationale; all now done):**

1. **Proactive fit triage, not one-by-one clicking (the big one).** Current flow makes
   the user click each trial to check fit. Redesign: `Analyze` → classification + matched
   candidates → automatically (or one "Assess candidates" click) run the real per-criterion
   fit across the **top 3–5** candidates → annotate each trial with a fit badge (✅N ❓N ❌N)
   and sort by fit → clinician drills into one for the full table + 3-agent verify. Frame as
   **fit triage for clinician review, NOT discovery/recommendation** (stays inside the
   "not a trial finder" red line; candidate set still comes from condition-scoping). Cost:
   one Claude call per triaged trial (~15s) — cap at 3–5, stream progress, warm before demos.
2. **Fix case-switch + flow order (Q1/Q2).** Switching the case dropdown currently does NOT
   refetch trials (they only update on `Analyze`), which is confusing. On case switch: clear
   trials/fit and prompt "Analyze to match". Guide the flow so `Analyze` clearly comes first
   (fit of a given trial is order-independent, but the trial list + classification depend on
   Analyze).
3. **Reports must look like a REAL pathology/molecular chart (format is real, content mock).**
   Rebuild `patient.py` reports in real report structure: demographics / specimen / clinical
   history / gross + microscopic description / **named assay platforms** (NGS panel name, IHC
   clone IDs) / integrated diagnosis per WHO CNS5 / signing pathologist.
4. **Ground molecular markers in REAL public de-identified data (cBioPortal / TCGA).** Verified
   feasible: `https://www.cbioportal.org/api/studies/gbm_tcga` — 619 real de-identified GBM
   samples, no key. Pull a real sample's molecular profile (IDH/MGMT/EGFR/subtype), render it
   into the report, and **show the provenance in the UI** (e.g. "source: TCGA-06-XXXX,
   cBioPortal gbm_tcga" + link) — a real credibility win the user wants to show judges. TCGA is
   already de-identified at source (barcodes, no names). Boundary: TCGA gives real molecular +
   basic clinical only; the **clinical narrative (prior bevacizumab, recurrence), the "EGFR not
   yet tested" gate, and preferences are constructed** demo layers (no API has them) — label
   them as illustrative. Hybrid = real molecular (cited) + transparent constructed clinical layer.
5. **Move patient preferences OUT of the chart into the shared-decision layer (Day 5).** A real
   chart never contains "prefers not to travel". Preferences (travel / QoL vs aggressive /
   caregiver / phase wariness / financial) are captured in a **separate Day 5 form, entered by
   the patient (doctor-guided)** — not in `patient.py` reports. Strip the preference sentences
   currently leaking into the reports; keep only clinical facts (location may stay as a
   demographic/logistics fact, but drop "prefers/wary" wording).

**Day 5 — shared-decision workspace — ✅ DONE.** Full flow wired: report → classify
→ fit(triage) → verify → explain → preferences → summary.
- `POST /api/explain` — plain-language agent renders a trial's verified fit for the
  patient (~7th grade); honest (unknowns → questions to confirm, never "you are
  eligible"; not medical advice). UI: "Explain for patient" button + card in fit view.
- `POST /api/summary` — DETERMINISTIC preference re-rank of the deep-assessed
  candidates (`_preference_rerank`) + plain non-directive note. Every adjustment
  (travel vs home_state, earliest-phase wariness, QoL vs aggressive) shows a
  reason/delta. Prefs entered in a Day-5 form (travel/home_state/goal/phase1/
  caregiver/financial), NOT in the chart. Preferences **visibly re-rank** without
  discovery or recommendation (red lines held).
- `trials.py` now surfaces Phase + site States for the heuristics.
- Also (post-plan, agreed with user): candidate retrieval upgraded to an
  **exhaustive** Stage 0 (pull ALL recruiting trials, not top-N) + deterministic
  recall-preserving **Stage 1 pre-screen** (`prescreen.py` — hard-conflict
  deprioritize, never hide, reasons shown) + Stage 2 fit on top screen-clear N.
  Documented in PRD §11.3 (with ASCII diagram). Answers "what if the best trial is
  buried at #50" without becoming a finder.

**Day 6 (next) —** polish, lock the demo case, record 3-min video (`docs/demo_script.md`),
100–200 word summary, make repo public, submit before Jul 13 9pm ET. NOTE: nothing is
deployed to Render/Vercel yet — the live sites still run pre-refactor code; deploy the
batch (Days-5-prep + Day 5) before the demo.

**Optional:** a "drafting model" toggle (Sonnet 5 ↔ Haiku) to make the Case 001 verify-catch
reliable for the demo (honest capability-tiering, per the honest findings above).

**How to run locally:** backend `cd backend && ../.venv/bin/uvicorn app.main:app --reload --port 8000`; frontend `cd frontend && npm run dev` (needs `frontend/.env.local` NEXT_PUBLIC_API_URL=http://127.0.0.1:8000).

---

## How the user works (preferences)

- Communicates in Chinese; wants direct, decisive guidance — give a recommendation, not a survey. Works ~5–7h/day on this and wants steady, visible progress — bias to building over deliberating; don't stall in decision loops.
- Comfortable with frontend; less experienced with backend infra / SQL / deploy. When building: **write the SQL / connection / API / deploy boilerplate for them**; they run it, check output, report errors. Explains trade-offs when asked, but expects a clear recommendation to act on.
- Has a biomedical family member (brother) as a domain reviewer — some docs are in Chinese for him. His wife has IDH-mutant glioma; handle the topic with care.
- Iterated heavily on positioning — the decisions above are hard-won; don't reopen without new information.
- Commits use name `touyuumiyabi`, email `tangxiya9906@gmail.com`, ending with the Claude co-author trailer. Original planning repo: `tangxiya-star/abridge-anthropic`.
