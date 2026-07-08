# GBM Shared Decision Evidence Copilot — Demo Script

> For the Abridge hackathon. Core framing: **the trial decision is not one conversation — it's several, across people and touchpoints. Our copilot stitches those scattered, verified pieces into one source-grounded shared-decision note.**

---

## 0. The 20-second hook (say this first)

> "Deciding on a glioblastoma trial isn't a single appointment. It's an in-person visit where the family says 'we can't travel out of state,' a tumor board the patient never sees, and a coordinator call about eligibility — spread across days. Today nobody stitches those together, and nothing is verifiable. We do both."

Why this wins with Abridge judges: it's a **conversation → verified documentation** story (Abridge's core), not just a trial-search tool.

---

## 1. Setup (10s)

- Patient: **Mock Case 001** — 58 y/o, recurrent GBM, IDH-wildtype, MGMT methylated, prior surgery + radiation + temozolomide, lives in California.
- On screen: empty Clinician Workspace.
- Say: "Everything you'll see is synthetic — no PHI. But the trial data is live from ClinicalTrials.gov."

---

## 2. Touchpoint A — the in-person conversation (45s)

Paste a short **synthetic transcript** into the copilot:

```
[Clinician] Your pathology came back — MGMT is methylated, which is
            good news for a few trials we can consider.
[Patient]   I really don't want to travel out of state. My husband can
            only be with me two days a week.
[Clinician] Understood. Let's prioritize what's here in California, and
            I'll be honest with you about what's experimental.
```

Show the copilot extract, with each item **linked back to the utterance**:
- Preference: *no out-of-state travel* → [transcript 00:14]
- Preference: *caregiver available 2 days/week* → [transcript 00:19]
- Clinical context: *MGMT methylated* → [transcript 00:03]

> Talking point: "This is the Abridge move — the patient's own words become structured, and every field is traceable to what was actually said."

---

## 3. Touchpoint B — evidence retrieval + verification (60s)

Copilot pulls live GBM trials and builds the evidence brief. Show the **three-agent loop** doing real work:

- **Drafting agent** writes: "Patient is eligible for Trial A."
- **Verification agent** flags it: *Ambiguous — disease and age match, but EGFR status unknown.*
- **Resolution**: reworded to "Potentially relevant; needs EGFR check."

> Talking point: "Claude never invents eligibility. It reasons only over retrieved ClinicalTrials.gov records, and the verification agent catches the overclaim. This is the difference between a demo and something a clinician would trust."

Every claim in the brief carries a `[NCT…]` or `[Pathology]` citation. Point at one and click through.

---

## 4. Touchpoint C — tumor board (the piece the patient never sees) (20s)

Show a clinician-only note that the patient wasn't present for:

> "Tumor board favors Trial A pending EGFR; Trial C strong biologically but out-of-state."

> Talking point: "This decision happened in a room the patient will never be in. Normally it's lost. We capture it as another verified touchpoint — and it's about to matter."

---

## 5. The stitch — preference-aware ranking (30s)

The copilot merges the **in-person preferences** + **verified evidence** + **tumor board reasoning**:

| Rank | Trial | Medical fit | Preference fit | Why |
|------|-------|-------------|----------------|-----|
| 1 | Trial A | High | High | In-state (UCSF) + Phase II |
| 2 | Trial B | Medium | Medium | Local but Phase I |
| 3 | Trial C | High | Low | Requires Boston — conflicts with stated preference |

> Talking point: "Trial C is biologically the best match — and it drops to #3, *because the patient told us she can't travel*. That's shared decision-making, not an algorithm overriding the patient."

(Note for judges: the ranking is a heuristic sorting aid, **not** a recommendation or a validated score — consistent with our non-goals.)

---

## 6. The payoff — one source-grounded note (30s)

Generate the **Shared Decision Summary**. Emphasize it fuses three separate touchpoints into one document:

- Options discussed (with citations)
- Patient preferences (linked to her actual words)
- Open questions (confirm EGFR, contact Trial A coordinator, ask about travel support for C)
- Draft note ready for clinician review

> Closing line: "Three conversations, three sources, zero PHI, every claim traceable — one note the clinician signs. **We didn't help the AI pick a trial. We helped the team decide together, and we made the reasoning verifiable.**"

---

## 7. If a clinician judge pushes back — pre-loaded answers

- **"Isn't this just a trial matcher? Doctors already filter by IDH and get a pop-up list."** → Those tools do **discovery** — filter a few *structured* fields and return a list. We don't compete there; we take the candidate pool exhaustively and call it scoping, not matching. We fill the **last mile the clinician still does by hand after the list appears**: (1) check the *whole* record against the *whole* eligibility — 15–30 criteria, most of it free text a filter never reads — per criterion, cited; (2) surface what's **unknown/missing** as a next step; (3) **catch over-claims** (verify agent rewrites an over-stated "eligible" when a decisive criterion is actually unknown); (4) translate to plain language + a preference-aware shared-decision note. *Concrete:* a filter says our IDH-wildtype GBM patient "matches" recruiting GBM trials — but many **exclude prior bevacizumab**, which lives in the clinical narrative, not a filter field, so the match is **false**; our per-criterion fit catches it. From *"these trials may be relevant"* → *"why this one may or may not fit **this** patient, what's missing, and how you two decide."*
- **"Is this giving medical advice?"** → No. Non-goal by design. Language is "potentially relevant," "for clinician review." No survival prediction, no autonomous enrollment.
- **"Trial data goes stale."** → Every card shows source + last-updated + uncertainty state.
- **"Where do the conversations come from?"** → Synthetic for the demo (like the patient). In production this is ambient capture — in-person room audio or a telehealth call. Both are Abridge-native.
- **"Is the 92% a real score?"** → It's a heuristic sort label, not a validated eligibility probability. We deliberately avoid unsupported scoring.

---

## Timing

| Section | Time | Running |
|---------|------|---------|
| Hook | 0:20 | 0:20 |
| Setup | 0:10 | 0:30 |
| Touchpoint A (conversation) | 0:45 | 1:15 |
| Touchpoint B (evidence + verify) | 1:00 | 2:15 |
| Touchpoint C (tumor board) | 0:20 | 2:35 |
| The stitch (ranking) | 0:30 | 3:05 |
| Payoff (the note) | 0:30 | 3:35 |
| Q&A buffer | — | ~4:00 |

Fits a 4–5 minute slot with room for questions.
