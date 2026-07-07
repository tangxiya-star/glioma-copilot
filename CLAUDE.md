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
- **Drug-name normalization** *(revised Jul 7)*: **Claude extracts** drug mentions from free text → **RxNorm (via RxNav REST API, key-free) normalizes** them to a canonical RxCUI/ingredient, cached in Postgres. This grounds drug identity in an authoritative source (reinforces "Claude is not the source of truth"). **Tier 1** — do after the core lands. **ChEMBL (REST API)** adds mechanism/drug-class matching (e.g. "prior anti-VEGF therapy") — **Tier 2 stretch**, only if Tier 0+1 are solid.
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

## Current status & next steps

- **Done**: direction locked; PRD-v2 written; planning docs in `docs/`. Repo scaffolded.
- **Next**:
  1. (Optional) Regenerate a Chinese PRD synced to v2 for the family reviewer, if needed.
  2. Produce/execute the **6-day build**: live ClinicalTrials.gov + report parse → WHO classification → Trial Fit Assessment → 3-agent verification → two views (clinician primary, shared-decision) → deploy → record 3-min video.

---

## How the user works (preferences)

- Communicates in Chinese; wants direct, decisive guidance — give a recommendation, not a survey. Works ~5–7h/day on this and wants steady, visible progress — bias to building over deliberating; don't stall in decision loops.
- Comfortable with frontend; less experienced with backend infra / SQL / deploy. When building: **write the SQL / connection / API / deploy boilerplate for them**; they run it, check output, report errors. Explains trade-offs when asked, but expects a clear recommendation to act on.
- Has a biomedical family member (brother) as a domain reviewer — some docs are in Chinese for him. His wife has IDH-mutant glioma; handle the topic with care.
- Iterated heavily on positioning — the decisions above are hard-won; don't reopen without new information.
- Commits use name `touyuumiyabi`, email `tangxiya9906@gmail.com`, ending with the Claude co-author trailer. Original planning repo: `tangxiya-star/abridge-anthropic`.
