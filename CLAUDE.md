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
- **Store**: **Postgres** as the app datastore (hosted — Supabase/Neon). Not Neo4j.
- **Drug-name normalization**: let **Claude** handle it. Skip RxNorm/ChEMBL.
- **Regulatory**: openFDA JSON API is an optional groundedness add. **No FDA PDF parsing.**
- **Agents**: Claude API — extraction, WHO CNS5 classification, drafting, verification, investigation, plain-language.
- **Frontend**: single deployed app (Streamlit for near-zero frontend, or Next.js single page), public URL. Builder track requires shippable "software they could use without you in the room."
- **Out of scope for MVP** (someday north-star only): Neo4j, AACT, RxNorm/ChEMBL, FDA PDF parsing.
- **Depth goes into the reasoning/verification layer** (visible in a 3-min demo; scores on Claude Use + Depth + Demo), NOT into invisible data plumbing.

---

## File map

| File | What it is |
|------|-----------|
| **`docs/PRD-v2-full.md`** | **Canonical PRD** — full current direction. Start here. |
| `docs/PRD-v1-lean.md` | Earlier leaner PRD (compact architecture). Reference. |
| `docs/PRD-中文版.md` | Chinese PRD **— still OLD GBM framing; needs syncing to v2** (for the biomedical family reviewer). |
| `docs/one-day-demo.md` | Bare-minimum cut — closest to the actual MVP shape. |
| `docs/five-day-build.md` | Fuller build plan (AACT/RxNorm/openFDA) — reference; MVP uses live API + Postgres instead. |
| `docs/demo_script.md` | Pitch script + pre-loaded Q&A. |
| `docs/demo_data_pack.md` | Real trials aligned to a synthetic GBM case; rehearsal/fallback. |

---

## Current status & next steps

- **Done**: direction locked; PRD-v2 written; planning docs in `docs/`. Repo scaffolded.
- **Next**:
  1. (Optional) Sync `docs/PRD-中文版.md` to v2 for the family reviewer.
  2. Produce/execute the **6-day build**: live ClinicalTrials.gov + report parse → WHO classification → Trial Fit Assessment → 3-agent verification → two views (clinician primary, shared-decision) → deploy → record 3-min video.

---

## How the user works (preferences)

- Communicates in Chinese; wants direct, decisive guidance — give a recommendation, not a survey.
- Relative beginner on infra (no SQL). When building: **write the SQL / connection / API / boilerplate for them**; they run it, check output, report errors.
- Has a biomedical family member (brother) as a domain reviewer — some docs are in Chinese for him. His wife has IDH-mutant glioma; handle the topic with care.
- Iterated heavily on positioning — the decisions above are hard-won; don't reopen without new information.
- Commits use name `touyuumiyabi`, email `tangxiya9906@gmail.com`, ending with the Claude co-author trailer. Original planning repo: `tangxiya-star/abridge-anthropic`.
