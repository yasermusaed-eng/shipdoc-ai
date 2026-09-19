"""
pages/3_Escalation_Queue.py — Human-in-the-Loop Triage & Escalation Queue.

(Placeholder page — will be built in Prompt 4).
"""

import sys
from pathlib import Path
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(DATA_DIR))
sys.path.insert(0, str(SRC_DIR))

from ui_common import init_shared_state, render_sidebar

st.set_page_config(
    page_title="ShipDoc AI — Escalation Queue",
    page_icon="⚠️",
    layout="wide",
)

init_shared_state()
render_sidebar()

st.title("⚠️ Escalation Queue")
st.caption("Human-in-the-loop review interface for unreadable documents, missing attachments, and low-confidence predictions")

st.info("🚧 **Under Construction**: This module will be fully built in Prompt 4.")

results = st.session_state.get("results", [])
if results:
    escalated_count = sum(1 for r in results if r.get("escalate") is True)
    st.metric("Pending Escalation Cases", escalated_count)
