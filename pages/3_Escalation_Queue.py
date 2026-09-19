"""
pages/3_Escalation_Queue.py — Dedicated Human-in-the-Loop Triage & Escalation Interface.

Proves the "Ask for help" capability by isolating cases where the pipeline
safely abstained from guessing and requested human operator review with explicit reasoning.
"""

from datetime import datetime
import sys
from pathlib import Path
import streamlit as st

# Setup module resolution
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(DATA_DIR))
sys.path.insert(0, str(SRC_DIR))

from ui_common import init_shared_state, render_sidebar, get_inbox

st.set_page_config(
    page_title="ShipDoc AI — Escalation Queue",
    page_icon="⚠️",
    layout="wide",
)

# Initialize persistent session state across pages
init_shared_state()
render_sidebar()

# Session-state for mock resolved escalations
if "resolved_escalations" not in st.session_state:
    st.session_state["resolved_escalations"] = {}

inbox = get_inbox()
results = st.session_state.get("results", [])

if not results:
    st.markdown("---")
    st.error(
        "### 💭 No pipeline data loaded yet\n\n"
        "The inbox hasn't been processed. Please go to the **Dashboard** page and click "
        "**'Run pipeline'** to load results — then come back here to review escalated cases."
    )
    st.page_link("pages/1_Dashboard.py", label="Go to Dashboard → Run pipeline", icon="🚀")
    st.stop()

# 1. Filter results to only escalate == true
all_comparison_emails = [r for r in results if r.get("category") == "document_comparison"]
all_escalated = [r for r in results if r.get("escalate") is True]

total_comparisons = len(all_comparison_emails)
total_escalated = len(all_escalated)
resolved_ids = set(st.session_state["resolved_escalations"].keys())
pending_escalations = [r for r in all_escalated if r["email_id"] not in resolved_ids]

# 4. Top One-Line Summary
st.title("⚠️ Human-in-the-Loop Escalation Queue")
pct_escalated = (total_escalated / total_comparisons * 100) if total_comparisons else 0
st.markdown(
    f"### 🛡️ **{total_escalated} of {total_comparisons} document-comparison emails required human review ({pct_escalated:.1f}%).**"
)
st.caption(
    "To preserve total auditability, ShipDoc AI never silently guesses when attachments are missing, "
    "files are unreadable, or extraction confidence is low. It halts autonomous execution and surfaces "
    "the case here with an explicit, traceable reason."
)

st.divider()

# Quick Status Bar & Reason Filter
col_stat1, col_stat2, col_stat3, col_filter = st.columns([1.5, 1.5, 1.5, 3.5])
col_stat1.metric("Total Escalations", total_escalated)
col_stat2.metric("Pending Review", len(pending_escalations), delta=f"-{len(resolved_ids)} resolved" if resolved_ids else None)
