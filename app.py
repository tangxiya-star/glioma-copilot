"""Glioma Copilot — Day 0 hello world.

Purpose: prove the deploy path works end-to-end (local -> GitHub -> Streamlit
Community Cloud -> public URL) before there is any real logic to lose.
Day 1 replaces this with the first vertical slice.
"""

import streamlit as st

st.set_page_config(page_title="Glioma Copilot", page_icon="🧠", layout="centered")

st.title("🧠 Glioma Copilot")
st.caption("Clinical trial matching + verification copilot for glioma care")

st.success("✅ Deploy path is live. Day 0 complete.")

st.markdown(
    """
    **What this becomes over the next 6 days:**

    1. Paste a molecular pathology report → structured patient profile + WHO CNS5 classification
    2. Pull live recruiting glioma trials from ClinicalTrials.gov
    3. Per-criterion eligibility screening (met / not-met / unknown) with citations
    4. A three-agent loop that catches and rewrites its own overclaims
    5. A doctor-guided shared-decision workspace

    *This page is a placeholder to confirm deployment. Real features land tomorrow.*
    """
)

st.divider()
st.write("Build plan:", "`docs/six-day-build.md`")
