"""
app.py — ShipDoc AI Home / Landing Page.

Landing and story page for the Averis x Monash Hackathon 2026.
(Detailed story and narrative will be built in Prompt 2).
"""

import sys
from pathlib import Path
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(DATA_DIR))
sys.path.insert(0, str(SRC_DIR))

from ui_common import init_shared_state, render_sidebar

st.set_page_config(
    page_title="ShipDoc AI — Home",
    page_icon="🚢",
    layout="wide",
)

init_shared_state()
render_sidebar()

st.title("🚢 Welcome to ShipDoc AI")
st.caption("Averis × Monash Hackathon 2026 — Shipping Document Verification System")

st.markdown("""
### Automated Logistics Document Discrepancy & Verification Platform

Welcome to **ShipDoc AI**, an intelligent operations copilot designed to eliminate the manual 
**3–4x document cross-checking bottleneck** per shipment between Shipping Instructions (SI) 
and draft Bills of Lading (BL).

Use the sidebar navigation to explore:
- 📊 **1. Dashboard**: High-level operational metrics and pipeline execution.
- 📋 **2. Inbox Explorer**: Filterable email records and side-by-side 7-field SI vs. BL comparison with discrepancy highlights.
- ⚠️ **3. Escalation Queue**: Human-in-the-loop review queue for low-confidence or unreadable documents.
- 💡 **4. How It Works**: End-to-end architecture and operational workflow breakdown.

*(Landing page story will be built in Prompt 2)*
""")
