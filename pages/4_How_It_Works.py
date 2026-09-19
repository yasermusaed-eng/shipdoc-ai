"""
pages/4_How_It_Works.py — Architecture & Operational Workflow.

(Placeholder page — will be built in Prompt 5).
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
    page_title="ShipDoc AI — How It Works",
    page_icon="💡",
    layout="wide",
)

init_shared_state()
render_sidebar()

st.title("💡 How It Works")
st.caption("End-to-end architecture, deterministic cross-validation, and operational workflow")

st.info("🚧 **Under Construction**: This module will be fully built in Prompt 5.")
