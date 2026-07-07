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

- **Language/app**: **Python + Streamlit** (fastest to a deployed public URL, one language for UI + agents; ideal for a beginner). *If a frontend-capable teammate exists → Next.js single page for a more polished demo; otherwise Streamlit.*
- **DB**: **hosted Postgres** — **Neon** or **Supabase** (no local install).
- **Trials**: **live ClinicalTrials.gov v2 API** (`https://clinicaltrials.gov/api/v2/studies`), no key.
- **LLM**: **Claude API** (`anthropic` Python SDK). Model: Claude Sonnet 5 for the agent calls (fast + capable); escalate a call to Opus 4.8 only if reasoning quality needs it.
- **Deploy**: **Streamlit Community Cloud** (free, public URL, connects to the GitHub repo).
- **Secrets**: `.env` locally (gitignored); Streamlit Cloud secrets for deploy. Never commit the API key.

---

## Day 0 setup (do at kickoff, ~1h)

- [ ] Hosted Postgres created (Neon/Supabase); copy the connection string.
- [ ] Anthropic API key ready; confirm credits (hackathon usually provides them — check the Discord/guide).
- [ ] Python env: `anthropic`, `psycopg[binary]`, `requests`, `streamlit`, `python-dotenv`.
- [ ] `.env` with `ANTHROPIC_API_KEY`, `DATABASE_URL`.
- [ ] "Hello world" Streamlit app deployed to a **public URL** (proves the deploy path works before there's anything to lose).

*(Claude will generate each of these as copy-paste steps when you start.)*

---

## Day 1 (Mon Jul 7, half day — starts 12:30 ET) — thinnest vertical slice

Goal: one real trial, pulled live, shown in a deployed app, with one Claude call working.

- [ ] Hardcode one synthetic glioma patient (molecular report text) in the repo.
- [ ] Call ClinicalTrials.gov v2 API for `condition=glioma&status=RECRUITING`, pull ~20 trials; show titles in Streamlit.
- [ ] One Claude call: given the report text, extract structured markers (IDH, MGMT, etc.) → display.
- [ ] Redeploy.

**Definition of done**: deployed URL shows a synthetic patient's extracted markers + a list of real recruiting glioma trials pulled live.

---

## Day 2 (Tue Jul 8) — ingestion, classification, storage

Goal: paste a report → structured profile + WHO classification; trials stored in Postgres.

- [ ] **Extraction agent**: free-text molecular report → structured profile (markers, prior treatments, age, location), each field with the source span it came from.
- [ ] **WHO CNS5 classification** from the marker set (IDH status → glioblastoma vs astrocytoma vs oligodendroglioma; grade; note if an older "GBM" label is reclassified). Cite the classification logic.
- [ ] Postgres schema: `patients`, `trials`, `eligibility_results`. Store the pulled trials + patient.
- [ ] Streamlit: a "paste report" box → shows profile + classification card.

**Definition of done**: paste any synthetic glioma report → correct WHO classification + structured profile; candidate trials stored and queryable.

---

## Day 3 (Wed Jul 9) — Trial Fit Assessment (the core)

Goal: per-criterion eligibility screening for each candidate trial.

- [ ] For each trial, split its eligibility criteria into discrete inclusion/exclusion items.
- [ ] **Fit assessment**: for each criterion, judge **met / not-met / unknown (needs test X)** against the patient profile; handle **negation** ("no prior bevacizumab"); cite the eligibility text line for each verdict.
- [ ] **Clinician view**: per-trial fit table (criteria + verdict + citation), plus which biomarkers matter and logistical barriers (travel/visit frequency from trial locations).

**Definition of done**: clinician view shows, for real trials, each eligibility criterion as met/not-met/unknown with a citation — including at least one correctly-flagged "unknown, needs testing."

---

## Day 4 (Thu Jul 10) — Verification + investigation (the differentiator)

Goal: the three-agent loop that catches its own overclaims — the demo money-moment.

- [ ] **Drafting agent**: structured evidence brief per trial (each claim cited).
- [ ] **Verification agent**: check every claim against the source (trial record / profile); flag and **rewrite overstatements** (e.g. "eligible for Trial B" → "possibly relevant; requires EGFR testing to confirm"). Produce a visible **verification log**.
- [ ] **Investigation agent**: resolve missing criteria / ambiguous biomarker matches / conflicts; update the brief.
- [ ] Clinician view: show the verification log with the caught/rewritten claim.

**Definition of done**: on a demo case, the verification agent visibly catches a wrong/overstated claim and rewrites it, with the log shown in the UI.

---

## Day 5 (Fri Jul 11) — Shared decision workspace

Goal: doctor-guided patient view + preferences + shared decision summary.

- [ ] **Plain-language agent**: render the verified per-trial analysis into patient-friendly language (what it tests, why may/may-not fit, what participation involves, what's known/unknown, questions to ask).
- [ ] **Patient preference capture**: structured form (travel, QoL vs aggressive, caregiver support, visit burden, experimental-therapy interest, financial/lodging).
- [ ] **Shared decision summary**: options discussed + fit (why yes/why no) + preferences + open questions + next steps, all source-linked. Preferences visibly influence the summary.
- [ ] Wire the full flow: report → review → fit → verify → explain → preferences → summary.

**Definition of done**: full end-to-end flow runs on the deployed URL; changing a preference changes the shared-decision summary.

---

## Day 6 (Sat–Sun Jul 12–13) — polish, video, submit

Goal: a submittable package with a safety net. **Deadline: Jul 13, 9:00 PM ET.**

- [ ] Polish UI, harden error handling, lock in the demo case (align synthetic report to real trials — see `demo_data_pack.md`).
- [ ] Make the GitHub repo **public** (`gh repo edit tangxiya-star/glioma-copilot --visibility public`) and confirm an OSS license file is present.
- [ ] **Record the 3-min demo video** (adapt `demo_script.md`): report → fit assessment → the verification catch → plain-language + shared decision summary. Re-record until clean; keep a backup take.
- [ ] Write the **100–200 word summary**.
- [ ] Submit on the CV platform **with buffer** (aim for Jul 13 afternoon, not 8:55 PM).

**Definition of done**: video + public repo + summary submitted before the deadline.

---

## Cut-line (if behind schedule, drop in this order)

1. Investigation agent (keep drafting + verification).
2. Multiple demo cases → one polished case.
3. Preference *re-ranking* logic → preferences just annotate the summary.
4. Fancy UI → plain Streamlit components.

**Never cut**: the verification catch (Claude Use), per-criterion fit with citations (Depth), and a deployed working URL + video (Demo). Those are the score.

---

## Judging-criteria check (keep asking "does the demo show this?")

- **Impact 25%** — named clinician user; real workflow (review/verify/explain/document); preferences integrated.
- **Claude Use 25%** — three-agent verification catching its own overclaims; per-criterion reasoning with negation.
- **Depth 25%** — WHO CNS5 classification + met/not-met/unknown + honest missing-data handling.
- **Demo 25%** — deployed, cited, the "looks eligible → correctly flagged" moment, clinician→patient handoff.
