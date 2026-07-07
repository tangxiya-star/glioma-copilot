# Glioma Copilot

**Glioma Evidence Review & Shared Decision Copilot** — an AI copilot that helps neuro-oncology clinicians review, verify, assess-fit, explain, and document clinical-trial options for a specific glioma patient.

Built for **Built with Claude: Life Sciences** (Cerebral Valley × Anthropic × Gladstone Institutes) — **Builder Track**.

> This is **not** a "trial finder." Clinicians already know the trials. The value is: for a candidate trial and a specific patient, assess *fit* — which eligibility criteria are met, what's missing, which biomarkers matter, what logistical barriers and uncertainties remain — with every claim source-grounded and verified, then explain it in plain language and document the shared decision. The goal is never "AI recommends Trial A"; it's "AI summarizes why Trial A may or may not be appropriate, for clinician review."

## Status

Planning complete; build in progress (July 7–13 hackathon window). See `docs/` for the PRD and plans, and `CLAUDE.md` for full project context.

## Docs

- `docs/PRD-v2-full.md` — canonical PRD (start here)
- `docs/one-day-demo.md` — closest to the actual MVP shape (live API + Claude + synthetic patient)
- `docs/demo_script.md`, `docs/demo_data_pack.md` — pitch script + rehearsal data

## Stack (planned)

Live ClinicalTrials.gov v2 API · Postgres (hosted) · Claude API (extraction / WHO CNS5 classification / drafting / verification / investigation / plain-language) · single deployed web app.
