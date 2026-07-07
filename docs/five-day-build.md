# Five-Day Build Plan — "Full-Smart" Version

> Companion to `PRD-v2-full.md` (north star) and `one-day-demo.md` (bare-minimum cut).
> **This is the recommended real build**: the full multi-source, source-grounded stack, with the two highest-risk pieces swapped for safer equivalents so a first-timer can actually finish in 5 days.

---

## Who this plan assumes

- **Solo, full-time, ~6–8 focused hours/day.** Less than that → this won't finish; drop to `one-day-demo.md`.
- **No SQL background.** That's fine — every query you need is written out for you below and will be filled in as we build. You run them; you don't have to author them from scratch.
- The actual hackathon is one day; **these 5 days are pre-work** to build the data + backend, so the hackathon day is just app polish + demo.

---

## Scope: what's in, what's swapped, what's cut

Keeps the PRD's core promise — *every clinical fact traces to an authoritative source, Claude only reasons over retrieved records* — while removing the two first-timer time-sinks (Neo4j learning curve, FDA PDF parsing).

| PRD component | This plan | Why |
|---------------|-----------|-----|
| **AACT** (trial data) | ✅ **Do it** | The core real dataset. Hosted Postgres — connect and query, no download needed. |
| **RxNorm** (drug normalization) | ✅ **Do it** | REST API, small GBM drug list. Beginner-friendly. |
| **openFDA** (regulatory) | ✅ **Do it — JSON API only** | Real regulatory grounding. ⚠️ **No PDF parsing** — that's the trap. |
| **ChEMBL** (molecule metadata) | 🔶 **Optional, last** | Nice-to-have. Cut if time runs short. |
| **Neo4j** (evidence graph) | 🔶 **Postgres instead** | Postgres does ~80% of it. Migrate to Neo4j only if everything else is done. |
| **FastAPI backend** | ✅ Do it | Thin layer over the DB + Claude calls. |
| **Claude agents** | ✅ Do it | Drafting / Verification / Plain-language. The product's brain. |
| **Two UIs** (clinician + shared decision) | ✅ Do it, minimal | Single Next.js app or Streamlit. Function over polish. |

**Net effect for a judge:** still looks like the full multi-source grounded system. The swaps (Postgres vs Neo4j, openFDA API vs PDF) are invisible on stage.

---

## The tech, in plain terms (so you know what you're touching)

- **Postgres** — a normal SQL database (tables of rows). Where all your data lives. You'll `SELECT` from it.
- **AACT** — a *public, hosted Postgres database* that already contains all of ClinicalTrials.gov as tables. You connect to *their* server with credentials they give you for free, run a query, and copy the GBM trials into *your own* Postgres. (Register free at https://aact.ctti-clinicaltrials.org/)
- **RxNorm** — a web API (RxNav) that turns messy drug names into a standard ID (RxCUI). You send "Temodar", it returns the canonical drug + ID.
- **openFDA** — a web API returning FDA drug label/approval data as JSON. No login, no PDF.
- **ChEMBL** — a web API (with a Python client) for molecule/target metadata.
- **FastAPI** — a Python web framework; your backend endpoints.
- **Claude API** — the LLM doing extraction, matching reasoning, verification, and plain-language.

You only need to get *comfortable enough to run given queries and calls* — not master any of these.

---

## Day-by-day plan

### Day 1 — AACT → your Postgres (the foundation)
Goal: real GBM trials sitting in your own local database.

- [ ] Install Postgres locally (or use a free hosted one like Supabase/Neon — even easier, no local setup).
- [ ] Register for a free AACT account; get connection credentials.
- [ ] Connect to AACT and run the GBM filter query *(query provided when we build)*.
- [ ] Copy the ~50–200 matching trials into your own `trials` table.
- [ ] Sanity check: `SELECT count(*) FROM trials;` returns a real number.

**First-timer note:** the "connect to a database" step is where beginners lose hours (drivers, connection strings, SSL). Budget for it. I'll give you a copy-paste Python script that connects and pulls — you won't hand-write SQL plumbing.

**End-of-day win:** "I have N real recruiting GBM trials in my database."

---

### Day 2 — RxNorm + openFDA enrichment
Goal: drug names normalized, regulatory facts attached.

- [ ] List the ~15 drugs that appear in your GBM trials (temozolomide, bevacizumab, lomustine, selinexor, …).
- [ ] For each, call RxNav → get canonical name + RxCUI. Store in a `drugs` table.
- [ ] For each drug, call openFDA drug-label endpoint → get approval status + indication. Store in an `fda_records` table.
- [ ] Link trials → drugs (a simple join table).

**First-timer note:** both are plain HTTP GET requests returning JSON. I'll give you the exact request code. No PDFs, no auth.

**End-of-day win:** "Every drug in my trials has a standard ID and its FDA status."

---

### Day 3 — Relationships + matching logic
Goal: given a patient, the system returns candidate trials with reasons.

- [ ] Design the relationship tables in Postgres (trial↔drug, trial↔biomarker, trial↔location). *(Schema provided.)*
- [ ] Extract biomarker mentions from trial eligibility text (this is where Claude helps — no regex dictionary).
- [ ] Write the matching query/logic: mock patient profile → candidate trials + why-matched / why-not.
- [ ] Command-line test: feed Case 001, get a ranked candidate list out.

**End-of-day win:** "I type in a patient, I get real matched trials with reasons — no UI yet, but the brain works."

---

### Day 4 — Claude agents (the product's value)
Goal: the source-grounded reasoning + verification loop.

- [ ] **Extraction agent**: conversation transcript → structured preferences + context (with source spans).
- [ ] **Drafting agent**: writes the evidence brief, each claim cited to an NCT / FDA record.
- [ ] **Verification agent**: checks each claim against the DB records; flags/rewrites overclaims (⭐ the demo money-moment — e.g. "eligible for Trial B" → "needs EGFR check").
- [ ] **Plain-language agent**: clinician text → patient-friendly explanation.

**First-timer note:** these are Claude API calls with good prompts, not ML training. Straightforward once Day 1–3 give them real data to reason over.

**End-of-day win:** "The verification agent visibly catches a wrong claim and fixes it."

---

### Day 5 — UI + integration + rehearsal
Goal: something you can present, plus a safety net.

- [ ] Minimal UI: paste conversation → run → show trial cards, citations, verification log, shared-decision note. (Streamlit if you want near-zero frontend code; Next.js single page if you prefer web.)
- [ ] Wire the full flow end to end.
- [ ] Rehearse the demo (`demo_script.md`), prep the Q&A answers.
- [ ] **Record a backup video** — if live API/DB fails on stage, you still have a demo.
- [ ] 🔶 Only if time remains: add ChEMBL molecule data, or migrate Postgres → Neo4j.

**End-of-day win:** "Full flow runs, I've rehearsed it, and I have a backup video."

---

## Where a first-timer actually loses time (plan for these)

1. **Connecting to a database** (drivers, connection strings, SSL) — Day 1. Biggest silent time-sink. → Use a hosted Postgres (Supabase/Neon) to skip local install pain.
2. **API responses not matching the docs** — RxNorm/openFDA JSON is nested and messy. → I'll give you tested parsing code.
3. **"It works in the tutorial in 30 min"** — your first time is 3× that. Estimate accordingly; don't pack the days tight.
4. **Chasing polish** — resist. Function first, pretty never (for a hackathon).

**Rule:** if any single step eats more than ~3 hours, stop and fall back to the `one-day-demo.md` equivalent for that piece (e.g. static JSON instead of AACT). Never let one tool sink the whole build.

---

## How I help (since you don't have SQL)

For each step above I can generate, when you start it:
- A **copy-paste connection script** (Python) so you never hand-write DB plumbing.
- The **exact SQL queries** — you run them, I explain what each does in one line.
- **Tested API request + parsing code** for RxNorm / openFDA / ChEMBL.
- The **agent prompts** for the Claude calls.

You drive; I write the SQL and the boilerplate. Your job is to run things, check outputs, and tell me what breaks.

---

## Honest risk summary

- **Solo, full-time, disciplined, using hosted Postgres** → achievable, but tight. No slack days.
- **If days are partial / interrupted** → you won't finish the full stack; pre-decide which tier to keep (AACT + RxNorm are the must-haves; openFDA/ChEMBL/Neo4j are droppable).
- **The two things that would blow the timeline** — Neo4j and FDA PDFs — are already swapped out of this plan. Keep them out unless everything else is done.

Bottom line: the full-smart version is the right level of ambition for a real build, and it's finishable in 5 focused days **because** the two beginner-killers are removed. Keep the PRD as the north star for what "done, someday" looks like.
