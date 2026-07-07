"""Deterministic WHO CNS5 (2021) classifier for adult-type diffuse gliomas.

The classification DECISION is a hardcoded rule engine — not a model guess — so
it is auditable and defensible. Claude's only job upstream is to read the
free-text report into the normalized `profile` this consumes (with source spans).

Rules (simplified adult-type diffuse glioma pathway, WHO CNS5 2021):
  1. IDH-mutant + 1p/19q co-deleted        -> Oligodendroglioma, IDH-mutant & 1p/19q-codeleted
  2. IDH-mutant + 1p/19q intact            -> Astrocytoma, IDH-mutant
       grade 4 if CDKN2A/B homozygous deletion, OR microvascular proliferation, OR necrosis
  3. IDH-wildtype astrocytic + ANY of      -> Glioblastoma, IDH-wildtype, grade 4
       {microvascular proliferation, necrosis, TERT promoter mutation,
        EGFR amplification, +7/-10 chromosome copy-number changes}

Key CNS5 point surfaced to the user: an IDH-wildtype astrocytoma with these
molecular/histologic features is classified GLIOBLASTOMA even without the older
histology-only definition — i.e. molecular features can upgrade the diagnosis.
"""

from typing import Any

WHO_SOURCE = "WHO Classification of CNS Tumours, 5th ed. (2021), adult-type diffuse gliomas"

# A profile field is one of these normalized enums (or "unknown").
# idh: mutant | wildtype
# codeletion_1p19q: codeleted | intact
# cdkn2a_b: homozygous_deletion | retained
# egfr_amp: amplified | not_amplified
# tert_promoter: mutated | wildtype
# chr7_10: gain7_loss10 | no
# microvascular_proliferation / necrosis: present | absent


def _val(profile: dict[str, Any], key: str) -> str:
    field = profile.get(key)
    if isinstance(field, dict):
        return str(field.get("value", "unknown")).lower()
    return str(field or "unknown").lower()


def _src(profile: dict[str, Any], key: str) -> str | None:
    field = profile.get(key)
    return field.get("source") if isinstance(field, dict) else None


def classify_who_cns5(profile: dict[str, Any]) -> dict[str, Any]:
    """Apply WHO CNS5 rules to a normalized profile; return a cited decision."""
    reasoning: list[dict[str, Any]] = []

    def step(rule: str, basis: str, key: str | None = None):
        reasoning.append(
            {"rule": rule, "basis": basis, "source": _src(profile, key) if key else None}
        )

    idh = _val(profile, "idh")

    if idh == "unknown":
        return {
            "diagnosis": "Indeterminate — IDH status required",
            "grade": None,
            "reasoning": [
                {"rule": "IDH status is the first branch point", "basis": "IDH not reported", "source": None}
            ],
            "reclassification_note": None,
            "source": WHO_SOURCE,
        }

    if idh == "mutant":
        step("IDH-mutant → IDH-mutant glioma pathway", "IDH mutant", "idh")
        codel = _val(profile, "codeletion_1p19q")
        if codel == "codeleted":
            step("IDH-mutant + 1p/19q co-deleted → Oligodendroglioma", "1p/19q co-deleted", "codeletion_1p19q")
            diagnosis = "Oligodendroglioma, IDH-mutant and 1p/19q-codeleted"
            grade = _grade_oligo_astro(profile, step)
            note = None
        else:
            step("IDH-mutant + 1p/19q intact → Astrocytoma, IDH-mutant", "1p/19q intact/not co-deleted", "codeletion_1p19q")
            diagnosis = "Astrocytoma, IDH-mutant"
            grade = _grade_oligo_astro(profile, step)
            note = None
        return {"diagnosis": diagnosis, "grade": grade, "reasoning": reasoning,
                "reclassification_note": note, "source": WHO_SOURCE}

    # IDH-wildtype astrocytic pathway
    step("IDH-wildtype astrocytic → assess glioblastoma-defining features", "IDH wild-type", "idh")
    gbm_features = []
    if _val(profile, "microvascular_proliferation") == "present":
        gbm_features.append(("microvascular proliferation", "microvascular_proliferation"))
    if _val(profile, "necrosis") == "present":
        gbm_features.append(("necrosis", "necrosis"))
    if _val(profile, "tert_promoter") == "mutated":
        gbm_features.append(("TERT promoter mutation", "tert_promoter"))
    if _val(profile, "egfr_amp") == "amplified":
        gbm_features.append(("EGFR amplification", "egfr_amp"))
    if _val(profile, "chr7_10") == "gain7_loss10":
        gbm_features.append(("+7/−10 CNV", "chr7_10"))

    if gbm_features:
        for label, key in gbm_features:
            step(f"GBM-defining feature present: {label}", label, key)
        note = (
            "Under WHO CNS5, an IDH-wildtype diffuse astrocytic glioma with any of "
            "these molecular/histologic features is classified GLIOBLASTOMA, grade 4 "
            "— even without the older histology-only definition."
        )
        return {"diagnosis": "Glioblastoma, IDH-wildtype", "grade": 4, "reasoning": reasoning,
                "reclassification_note": note, "source": WHO_SOURCE}

    step("No GBM-defining feature found", "none of MVP/necrosis/TERT/EGFR-amp/+7−10 present")
    return {
        "diagnosis": "Diffuse astrocytic glioma, IDH-wildtype (grade pending molecular workup)",
        "grade": None,
        "reasoning": reasoning,
        "reclassification_note": (
            "No glioblastoma-defining molecular feature reported yet; recommend TERT / "
            "EGFR / chromosome 7&10 testing before finalizing grade."
        ),
        "source": WHO_SOURCE,
    }


def _grade_oligo_astro(profile: dict[str, Any], step) -> int | None:
    """Grade for IDH-mutant tumors: 4 if CDKN2A/B homozygous deletion or necrosis/MVP."""
    if _val(profile, "cdkn2a_b") == "homozygous_deletion":
        step("CDKN2A/B homozygous deletion → grade 4", "CDKN2A/B homozygous deletion", "cdkn2a_b")
        return 4
    if _val(profile, "necrosis") == "present" or _val(profile, "microvascular_proliferation") == "present":
        step("Necrosis / microvascular proliferation → higher grade", "necrosis or MVP present")
        return 4
    return None  # grade 2 vs 3 needs mitotic detail not modeled here
