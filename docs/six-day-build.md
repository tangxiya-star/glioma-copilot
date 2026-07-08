# Six-Day Build Plan — July 7–13

> The execution plan for the hackathon window. Stack is locked (see `../CLAUDE.md`): **live ClinicalTrials.gov v2 API + hosted Postgres + Claude API + one deployed web app**. Two views: clinician (primary) + doctor-guided shared decision.
>
> **Guiding principles**
> 1. **Thin vertical slice first** — get a real end-to-end path deployed on Day 1, then deepen. Always have something demoable.
> 2. **Depth goes into the reasoning/verification layer**, not data plumbing (that's where Claude Use + Depth + Demo score).
> 3. **Deploy early, redeploy often** — a public URL from Day 1, not Day 6.
> 4. **The user runs code; Claude writes the SQL / API / boilerplate.** (User is a SQL/infra beginner.)
> 5. **3-hour rule**: if any single piece stalls >3h, ship the simpler fallback and move on.

---

## Stack (decided — don't re-debate)

Matches the full PRD §13, with **Postgres in place of Neo4j** for the hackathon window. Decided Jul 7 — builder knows frontend, so we run the PRD's real stack rather than the Streamlit fallback.

- **Frontend**: **Next.js / React + Tailwind CSS + shadcn/ui** (Framer Motion optional). Clinician workspace, shared-decision workspace, patient-preference form, trial cards, evidence citations.
- **Backend**: **FastAPI (Python) + Pydantic**. API endpoints, trial retrieval, evidence-bundle construction, agent orchestration.
- **DB**: **hosted Postgres — Neon** (no local install; already provisioned). Relationships (drug / trial / biomarker / sponsor / location / patient) modeled with SQL tables + joins, **not Neo4j** (deferred post-hackathon).
- **Trials**: **live ClinicalTrials.gov v2 API** (`https://clinicaltrials.gov/api/v2/studies`), no key.
- **LLM**: **Claude API** (`anthropic` Python SDK, called from the FastAPI backend). Model: Claude Sonnet 5 for the agent calls (fast + capable); escalate a call to Opus 4.8 only if reasoning quality needs it. **Claude is not the source of truth — it only reasons over retrieved records.**
- **Data processing**: Python + `requests` (ClinicalTrials.gov ingestion, eligibility text extraction); `pandas` only if needed.
- **Deploy**: **frontend → Vercel**; **backend → Render / Railway / Fly.io** (free tier, public URL, redeploys on push from the GitHub repo).
- **Secrets**: `.env` locally (gitignored); host-dashboard secrets for deploy (Vercel env vars for the frontend, backend-host env vars for `ANTHROPIC_API_KEY` + `DATABASE_URL`). Never commit the API key.

---

## Day 0 setup (do at kickoff, ~1h)

- [ ] Hosted Postgres created (Neon/Supabase); copy the connection string.
- [ ] Anthropic API key ready; confirm credits (hackathon usually provides them — check the Discord/guide).
- [ ] Backend Python env: `fastapi`, `uvicorn`, `anthropic`, `psycopg[binary]`, `requests`, `pydantic`, `python-dotenv`.
- [ ] Frontend: `npx create-next-app` (TypeScript + Tailwind), add shadcn/ui.
- [ ] `.env` with `ANTHROPIC_API_KEY`, `DATABASE_URL`.
- [ ] "Hello world" deployed to **public URLs**: frontend on Vercel + backend `/health` on Render/Railway/Fly (proves the deploy path works before there's anything to lose).

*(Claude will generate each of these as copy-paste steps when you start.)*

---

> **Progress note (updated Jul 7):** work moved much faster than the day-by-day plan —
> Days 1→5 all landed, plus an added UX/credibility refactor, exhaustive candidate
> triage, real TCGA provenance, and the RxNorm+ChEMBL drug layer (see Day 4.5). Boxes
> below are checked to reflect what's actually built + committed on `main` and deployed.

## Day 1 — thinnest vertical slice — ✅ DONE

Goal: one real trial, pulled live, shown in a deployed app, with one Claude call working.

- [x] Synthetic glioma patient (molecular report) hardcoded (`patient.py`).
- [x] Backend: ClinicalTrials.gov v2 live fetch (`trials.py`); FastAPI endpoint; frontend shows trials.
- [x] Claude call: report → structured markers (`POST /api/extract`).
- [x] Deployed both ends (Vercel + Render).

**Done**: deployed URL shows a synthetic patient's markers + real recruiting trials pulled live.

---

## Day 2 — ingestion, classification, storage — ✅ DONE

Goal: report → structured profile + WHO classification; trials stored in Postgres.

- [x] **Extraction** → structured profile with source spans.
- [x] **Deterministic WHO CNS5 classifier** (`classify.py`): Claude normalizes the report → a hardcoded rule engine decides the diagnosis (grounds "Claude is not the source of truth").
- [x] Postgres schema (`patients`, `trials`, `eligibility_results`) + storage (`db.py`, `schema.sql`).
- [x] Frontend: report box → profile + classification card with cited reasoning.

**Done**: any synthetic glioma report → correct WHO classification + profile; trials stored/queryable.

---

## Day 3 — Trial Fit Assessment (the core) — ✅ DONE

Goal: per-criterion eligibility screening for each candidate trial.

- [x] Split eligibility into inclusion/exclusion items.
- [x] **Fit assessment**: each criterion **met / not-met / unknown**, with **negation** handling and the eligibility line **cited** (`POST /api/fit` + `/api/fit/stream`, NDJSON streamed one criterion at a time).
- [x] Patient-matched retrieval (condition derived from the diagnosis).
- [~] RxNorm (Tier 1) + ChEMBL (Tier 2) drug normalization — **deferred here, later built in full** (see **Day 4.5**).

**Done**: clinician view shows each criterion as met/not-met/unknown with a citation, incl. a correctly-flagged "unknown, needs testing" (Case 001 EGFR).

---

## Day 4 — Verification + investigation (the differentiator) — ✅ DONE

Goal: the three-agent loop that catches its own overclaims — the demo money-moment.

- [x] **Drafting agent**: cited evidence brief per trial.
- [x] **Verification agent** (Opus): checks every claim vs the fit assessment; **rewrites overstatements** ("eligible" → "possibly relevant; requires EGFR testing").
- [x] **Investigation agent**: concrete next steps for unknown/flagged items.
- [x] Clinician-view verification log (`POST /api/review/stream`, streamed).

**Done**: on a demo case the verify agent visibly catches + rewrites an overclaim, log shown in UI.

---

## Day 4.5 — UX/credibility refactor + exhaustive triage + drug layer — ✅ DONE (added Jul 7)

Not in the original plan; added after reviewing the build with fresh eyes. All committed + deployed.

- [x] **Proactive fit triage** — Analyze auto-runs the real fit across candidates and badges/sorts them (no more one-by-one clicking).
- [x] **Exhaustive 3-stage candidate triage** (`/api/triage/stream`, PRD §11.3): **Stage 0** pull *every* recruiting trial for the tumor type (not a top-N slice; glioblastoma ≈ 326) → **Stage 1** deterministic, recall-preserving pre-screen (`prescreen.py`) deprioritizes hard conflicts with reasons, never hides → **Stage 2** real fit on the top screen-clear N; UI shows "deep-assessed N of total". Answers "what if the best trial is buried at #50" without becoming a finder.
- [x] **Flow order fix** — trials gated behind Analyze; case-switch clears stale results; instant in-memory case switching.
- [x] **Real pathology-report format** — reports rebuilt as integrated neuropathology charts (named IHC clones, assay platforms, WHO CNS5 integrated dx, sign-out).
- [x] **Real molecular provenance** — each case maps to a **real de-identified TCGA sample** (cBioPortal `lgggbm_tcga_pub`, Cell 2016); real markers + variant calls; UI provenance card + clickable link. Constructed clinical layer clearly labeled.
- [x] **Preferences out of the chart** — moved to the Day-5 form.
- [x] **RxNorm (Tier 1) + ChEMBL (Tier 2) drug normalization** (`drugs.py`, from Day 3 backlog): Claude names the drug → RxNorm → canonical ingredient/RxCUI → ChEMBL mechanism/class (Temodar/TMZ → temozolomide; bevacizumab → "VEGF-A inhibitor"). Postgres-cached; `POST /api/drugs/normalize` + `/api/drugs/from_patient`; UI card after Analyze. PRD §12.2.
- [x] **Docs** — PRD §4.1 (why existing trial matchers don't close the gap), §11.3 (retrieval/screen/triage pipeline + ASCII diagram), §12.2 (drug layer); demo script rewritten to match the real build.

---

## Day 5 — Shared decision workspace — ✅ DONE

Goal: doctor-guided patient view + preferences + shared decision summary.

- [x] **Plain-language agent** (`POST /api/explain`): renders the verified per-trial fit for the patient (~7th grade); honest (unknowns → questions to confirm, never "you are eligible"; not medical advice). UI: "Explain for patient" card.
- [x] **Preference capture** form (travel / home state / goal QoL↔aggressive / phase-1 wariness / caregiver / financial) — entered here, **not** in the chart.
- [x] **Shared-decision summary** (`POST /api/summary`): DETERMINISTIC preference re-rank (`_preference_rerank`) with every adjustment's reason/delta shown, + a plain non-directive note. Preferences **visibly re-rank** without discovery or recommendation.
- [x] Full flow wired: report → classify → fit(triage) → verify → explain → preferences → summary.

**Done**: full end-to-end flow runs on the deployed URL; changing a preference visibly re-ranks the summary.

---

## Day 6 (next) — polish, video, submit

Goal: a submittable package with a safety net. **Deadline: Jul 13, 9:00 PM ET.**

- [x] Deployed and verified end-to-end on the live URLs (front Vercel + back Render).
- [ ] Polish UI, harden error handling, lock in the demo case (see `demo_data_pack.md` — may need aligning to the current build).
- [ ] Make the GitHub repo **public** (`gh repo edit tangxiya-star/glioma-copilot --visibility public`) + confirm an OSS license file is present. **(Still private.)**
- [ ] **Record the 3-min demo video** — follow the rewritten `demo_script.md` (report → classify → exhaustive triage → fit + verify catch → explain + shared decision). Warm `/health` first (Render sleeps).
- [ ] Write the **100–200 word summary**.
- [ ] Submit on the CV platform **with buffer** (Jul 13 afternoon, not 8:55 PM).

**Definition of done**: video + public repo + summary submitted before the deadline.

---

## Cut-line (if behind schedule, drop in this order)

> **Moot as of Jul 7 — nothing was cut.** All of the below shipped: ChEMBL + RxNorm
> (Day 4.5), investigation agent (Day 4), 4 demo cases, and full preference *re-ranking*
> (Day 5). Kept for reference.

1. ChEMBL mechanism/class match (Tier 2 stretch) — drop first. → **built**.
2. RxNorm normalization (Tier 1) → fall back to Claude-only drug matching. → **built**.
3. Investigation agent (keep drafting + verification). → **built**.
4. Multiple demo cases → one polished case. → **4 cases built**.
5. Preference *re-ranking* logic → preferences just annotate the summary. → **full re-rank built**.
6. Fancy UI → plain shadcn/ui components, minimal styling.

**Never cut**: the verification catch (Claude Use), per-criterion fit with citations (Depth), and a deployed working URL + video (Demo). Those are the score.

---

## Judging-criteria check (keep asking "does the demo show this?")

- **Impact 25%** — named clinician user; real workflow (review/verify/explain/document); preferences integrated.
- **Claude Use 25%** — three-agent verification catching its own overclaims; per-criterion reasoning with negation.
- **Depth 25%** — WHO CNS5 classification + met/not-met/unknown + honest missing-data handling.
- **Demo 25%** — deployed, cited, the "looks eligible → correctly flagged" moment, clinician→patient handoff.
