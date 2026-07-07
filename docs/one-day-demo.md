# One-Day Demo Plan

> Companion to the full PRD. The PRD (`PRD-v2-full.md`) stays the north star — Neo4j graph, RxNorm/ChEMBL normalization, FDA parsing, AACT, 5-day build. **This file is the cut-down version for a single-day hackathon.** Same product story, radically less infrastructure.

---

## The core constraint

One day. So the rule is: **keep only what can be demoed and scored; replace all heavy infrastructure with the lightest thing that preserves realness.**

Two traps to avoid:
1. **Over-building infra** — Neo4j / RxNorm API / FDA PDF parsing / AACT will eat the whole day and you'll have nothing to show.
2. **A fake-looking demo** — if the pipeline is lookup tables and pre-aligned data, judges see through it and a new case breaks it live.

The resolution: **real trial retrieval + real Claude reasoning + synthetic patient.** Not "all mock."

---

## What's real vs synthetic (this matters)

| Thing | Real or synthetic | Why |
|-------|-------------------|-----|
| **Clinical trial data** | ✅ **Real** — live ClinicalTrials.gov v2 API | Public API, no key. Querying it live proves the demo isn't hardcoded. |
| **Trial matching / eligibility reasoning** | ✅ **Real** — Claude reads eligibility text | Not a lookup table. Generalizes to any new case. |
| **Verification / note generation** | ✅ **Real** — Claude | The product itself. |
| **Patient + conversation** | ⚠️ **Synthetic** | Required — real PHI can't clear HIPAA. Every health hackathon uses synthetic patients. Not a weakness. |

---

## What we cut from the PRD (infrastructure only — not "realness")

| PRD component | One-day replacement |
|---------------|--------------------|
| Neo4j graph | Python dict / in-memory JSON |
| RxNorm + ChEMBL normalization | **Nothing** — Claude already knows TMZ = Temodar = temozolomide |
| FDA PDF parsing | Not in demo |
| AACT / bulk ingestion | Live ClinicalTrials.gov v2 API on demand |
| Biomarker dictionary | **Claude reads eligibility text directly** |
| Multiple patients | One (plus live-improvised cases, see below) |

**Key principle: lean MORE on Claude, LESS on hardcoded lookups.** It's both more general AND less work for one day. The only lookup tables we'd hardcode (drug dict, biomarker dict) are exactly the things that break on a new case — so we skip them.

---

## The pipeline (4 Claude calls + live retrieval + one page)

```
[synthetic conversation]
        │  Claude call 1: extract preferences + clinical context (with source timestamps)
        ▼
[structured patient profile]
        │  LIVE: ClinicalTrials.gov v2 API — query by condition/status
        ▼
[real trial records]
        │  Claude call 2: match + eligibility reasoning, each claim cited to NCT
        ▼
[evidence brief]
        │  Claude call 3: verification pass — catch overclaims, reword (THE money moment)
        ▼
[verified brief]
        │  Claude call 4: patient-friendly explanation + shared decision note
        ▼
[source-grounded shared decision note]
```

Every step except retrieval is Claude reasoning — so it generalizes. Retrieval is a live public API call — so it's provably real.

---

## One-day timeline (replaces the PRD's 5-day plan)

```
Morning (0–3h)  Static: synthetic patient + transcript text.
                Wire the live ClinicalTrials.gov v2 API call.
                Write the 4 Claude prompts; get correct output on the command line.
Midday (3–5h)   Simplest possible UI: paste conversation → button → show results.
                Streamlit OR a single HTML page. Do NOT chase polish.
Afternoon (5–7h) Connect the full flow end to end.
                The verification step MUST visibly "catch an overclaim → reword."
Evening (7–8h)  Rehearse the demo script, prep Q&A, record a backup video
                in case the live API/network fails on stage.
```

---

## The generalization test (the mic-drop move)

Because the engine is Claude + live retrieval (no lookup tables), you can invite this on stage:

> "Don't use our prepared case. **Make up a GBM patient right now** — age, markers, prior treatment, state — and I'll type it in."

The system queries ClinicalTrials.gov live, Claude reasons, a note comes out. **Surviving an improvised new case proves it isn't scripted.**

⚠️ Precondition: this ONLY works if there are zero hardcoded shortcuts (no drug dict, no pre-aligned trial narrative). If you bake in lookup tables, a live new case crashes. So the architecture choice is forced: **to dare a live case swap, the engine must be pure Claude + live retrieval.**

---

## Role of `demo_data_pack.md` under this plan

It's no longer "the system's data" — it becomes the **rehearsal / fallback script**:
- Rehearse on it — guarantees one path that runs smoothly and tells a strong story (real trials, real reasoning, just a curated case).
- If judges don't improvise → run this scripted path.
- If judges improvise → switch to live-case mode to prove generalization.

Best of both: a safe path and a proof-of-realness path.

---

## Open decisions (settle before coding)

- **Solo or team?** Changes how much UI polish is realistic.
- **Python or JS strength?** → Python/backend → Streamlit (almost no frontend code). JS/frontend → Next.js single page calling the Claude API.
- **Live API on stage, or pre-fetched with a live fallback?** Recommend: live by default, keep a cached JSON + recorded video as backup for network failure.

---

## Bottom line

The one-day version keeps the PRD's *story and value* (conversation → verified, source-grounded shared-decision note) while dropping only the *infrastructure weight*. Trials stay real (live API), reasoning stays real (Claude), patient stays synthetic (required). Skip the lookup tables and it generalizes to any new case — which is exactly what makes it demo-proof.
