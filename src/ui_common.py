"""
ui_common.py — Shared utilities, session state persistence, and sidebar navigation branding.
"""

import json
import sys
from pathlib import Path
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
SRC_DIR = PROJECT_ROOT / "src"
OUTPUT_DIR = PROJECT_ROOT / "output"
RESULTS_PATH = OUTPUT_DIR / "results.json"
SUBMISSION_PATH = OUTPUT_DIR / "submission.json"

sys.path.insert(0, str(DATA_DIR))
sys.path.insert(0, str(SRC_DIR))

try:
    from loader import Inbox
except ImportError:
    from data.loader import Inbox


def get_inbox():
    """Returns singleton-like Inbox instance for dataset reading."""
    return Inbox(str(DATA_DIR))


def init_shared_state():
    """Initializes and persists pipeline results across Streamlit pages."""
    if "results" not in st.session_state or st.session_state["results"] is None:
        if RESULTS_PATH.exists():
            try:
                with open(RESULTS_PATH, "r", encoding="utf-8") as f:
                    st.session_state["results"] = json.load(f)
            except Exception:
                st.session_state["results"] = []
        else:
            st.session_state["results"] = []


def render_sidebar():
    """Renders the consistent logo, title, and dataset status in the sidebar across all pages."""
    st.sidebar.markdown("## 🚢 ShipDoc AI")
    st.sidebar.caption("Shipping Document Verification System  \n**Averis × Monash Hackathon 2026**")
    st.sidebar.divider()

    results = st.session_state.get("results", [])
    if results:
        total = len(results)
        mismatches = sum(1 for r in results if r.get("mismatch_found") is True)
        escalated = sum(1 for r in results if r.get("escalate") is True)
        
        st.sidebar.markdown(f"**Dataset Status:**  \n`{total}` emails loaded")
        st.sidebar.markdown(f"- 🚨 Mismatches: `{mismatches}`")
        st.sidebar.markdown(f"- ⚠️ Escalations: `{escalated}`")
    else:
        st.sidebar.info("No pipeline results in memory. Visit **Dashboard** to run the pipeline.")

    st.sidebar.divider()
    st.sidebar.caption("Prototype built for Averis ops team demo.")
