# Demo Data Pack — aligned to real ClinicalTrials.gov records

Everything below is **synthetic conversation** wrapped around **real, live trial records** (pulled from ClinicalTrials.gov v2 API). When a judge clicks a citation in the demo, it resolves to a real NCT record whose eligibility actually matches the mock patient. No PHI — the patient and the dialogue are invented; only the trials are real.

> ⚠️ Trial statuses/eligibility change. Re-pull these NCT records the morning of the demo and confirm still `RECRUITING` before you present.

---

## Mock Patient — Case 001

| Field | Value |
|-------|-------|
| Age | 58 |
| Diagnosis | Glioblastoma, **IDH-wildtype** |
| Disease state | **First recurrence** |
| Molecular | **MGMT promoter methylated**; EGFR status **unknown** (not yet tested) |
| Prior treatment | Surgery → radiation → **temozolomide** (standard first-line) |
| Performance | ECOG 1 (KPS ~80) |
| Location | California |
| Preferences | No out-of-state travel; caregiver 2 days/week; values QoL |

This profile was chosen because it cleanly matches Trial A's inclusion criteria and creates a real EGFR-gated ambiguity for Trials B and C.

---

## The three real trials

### Trial A — best match, in-state ✅
- **NCT05432804** — *Selinexor + Temozolomide for recurrent GBM* (NCI)
- **Phase I/II**, RECRUITING
- Condition: **Recurrent Glioblastoma, IDH-wildtype; MGMT-methylated** — exact patient match
- Key inclusion (real): histologically confirmed GBM IDH-wildtype / MGMT-methylated at **first recurrence**; must have had **first-line temozolomide + radiotherapy**; **no prior therapy for recurrence**; age ≥18; **ECOG ≤2**; **no prior bevacizumab**.
- California sites (real): **City of Hope**, **UC San Diego Moores**, **Keck/USC**, **UC Davis**, USC Norris, LA General.
- → Patient matches every inclusion line. High medical fit + high preference fit (in-state).

### Trial B — in-state but early phase, EGFR-gated ⚠️
- **NCT07089641** — *ERAS-801 (EGFR inhibitor) for progressive/recurrent GBM*
- **Phase I**, RECRUITING, **California**
- Targets **EGFR** — so eligibility depends on an EGFR result the patient doesn't have yet.
- → In-state (good), but Phase I (patient unsure about Phase I) and **eligibility unknown until EGFR tested** → this is the trial the verification agent flags as *ambiguous*.

### Trial C — strong biology, out-of-state ❌ for this patient
- **NCT07209241** — *CART-EGFR-IL13Rα2 CAR-T cells for recurrent GBM*
- **Phase I**, RECRUITING, **Pennsylvania** (UPenn) — out of state
- Cutting-edge cell therapy, biologically compelling for GBM.
- → High medical interest, but **requires travel out of California** → conflicts with the stated preference, drops in preference-aware ranking.

---

## Touchpoint A — synthetic in-person transcript (paste this into the copilot)

```
[00:03] [Clinician] Good news on part of your pathology — the MGMT marker
                    came back methylated. That actually opens up a couple
                    of trials that pair well with temozolomide.
[00:14] [Patient]  I have to be honest, I really don't want to travel out
                    of state. My husband can only be with me two days a week.
[00:19] [Caregiver] And the weekly driving is a lot on her already.
[00:26] [Clinician] Completely understood. Let's prioritize what's here in
                    California. There's one at City of Hope or UC San Diego
                    that fits your profile well.
[00:35] [Patient]  Is it one of the very experimental ones? I'm nervous
                    about the earliest-stage studies.
[00:41] [Clinician] Fair question. One combines an approved chemo with a
                    newer drug — that's the one I'd start with. There's also
                    an early cell-therapy trial, but it's in Pennsylvania,
                    so travel would be the issue there.
[00:52] [Clinician] There's a third option here in California, but it needs
                    an EGFR lab result we don't have yet — we'd have to test
                    for that first.
```

### What the extraction agent should pull (each linked to a timestamp)
| Extracted | Value | Source |
|-----------|-------|--------|
| Clinical context | MGMT methylated | [transcript 00:03] |
| Preference | No out-of-state travel | [transcript 00:14] |
| Preference | Caregiver 2 days/week | [transcript 00:14] |
| Preference | Wary of earliest-phase trials | [transcript 00:35] |
| Open question | EGFR status needed for Trial B | [transcript 00:52] |

---

## Touchpoint B — verification agent, worked example (real record)

- **Drafting agent** writes: *"Patient is eligible for Trial A (NCT05432804)."*
- **Verification agent** checks against the real eligibility record:
  - ✓ Recurrent GBM, IDH-wildtype — matches condition field
  - ✓ MGMT methylated — matches condition field
  - ✓ Prior temozolomide + radiation — matches inclusion
  - ✓ First recurrence, no prior recurrence therapy — matches inclusion
  - ✓ ECOG 1 (≤2 required) — matches inclusion
  - ✓ No prior bevacizumab — matches (patient never received it)
- **Verdict**: *Supported.* Trial A claim stands, fully cited to NCT05432804 eligibility.

Contrast with **Trial B (NCT07089641)**:
- **Drafting agent**: *"Patient is eligible for Trial B."*
- **Verification agent**: *Ambiguous — trial targets EGFR; patient's EGFR status is unknown.*
- **Resolution**: reworded to *"Potentially relevant; requires EGFR testing to confirm eligibility."*

This is the on-stage moment: the agent **catches an overclaim** and rewrites it. Real record, real gate.

---

## Touchpoint C — tumor board note (synthetic, clinician-only)

```
Tumor board — Case 001
Consensus: favor NCT05432804 (Selinexor + TMZ) — patient matches IDH/MGMT
and prior-therapy criteria, in-state sites available.
NCT07209241 (CAR-T, UPenn) biologically attractive but out-of-state.
Defer NCT07089641 pending EGFR testing.
```

The patient was **not present** for this. The copilot captures it as a third verified touchpoint — and it's what justifies the final ranking.

---

## The stitch — preference-aware ranking (all real trials)

| Rank | Trial | Medical fit | Preference fit | Why |
|------|-------|-------------|----------------|-----|
| 1 | **NCT05432804** Selinexor+TMZ | High | High | Exact IDH/MGMT match, in-state (City of Hope / UCSD) |
| 2 | **NCT07089641** ERAS-801 | Medium | Medium | In-state, but Phase I + EGFR unconfirmed |
| 3 | **NCT07209241** CAR-T | High | Low | Strong biology, but Pennsylvania — conflicts with no-travel preference |

> Money line: "The CAR-T trial is arguably the most exciting science on this list — and it's ranked third, **because the patient told us she can't travel.** The algorithm didn't override her; it documented her."

(Ranking is a heuristic sort aid, not a validated eligibility score — per non-goals.)

---

## Shared Decision Summary (the deliverable note)

```
Shared Decision Summary — Case 001

Options discussed:
• NCT05432804 (Selinexor + temozolomide, Phase I/II) — medically well-matched
  (IDH-wildtype, MGMT-methylated, prior TMZ+RT), recruiting in California.
• NCT07089641 (ERAS-801, Phase I) — in-state, but earlier-phase and requires
  EGFR testing to determine eligibility.
• NCT07209241 (CAR-T, Phase I) — biologically relevant, but located in
  Pennsylvania; out-of-state travel required.

Patient preferences (from conversation):
• Prefers to remain in California [transcript 00:14]
• Caregiver support limited to ~2 days/week [transcript 00:14]
• Cautious about earliest-phase experimental trials [transcript 00:35]

Open questions / next steps:
• Order EGFR testing (gates NCT07089641)
• Contact NCT05432804 coordinator re: visit schedule at City of Hope / UCSD
• Note NCT07209241 as travel-dependent; revisit only if travel support found

Draft note for clinician review:
Patient and clinician (with caregiver present) reviewed clinical trial options
for recurrent IDH-wildtype, MGMT-methylated glioblastoma. Patient expressed a
preference for in-state trials and concern about frequent travel and early-phase
studies. NCT05432804 identified as the leading in-state option; NCT07089641
pending EGFR result. All trial claims source-linked to ClinicalTrials.gov;
patient preferences source-linked to the visit conversation.
```

Every clinical claim → NCT citation. Every preference → transcript timestamp. Zero PHI.
