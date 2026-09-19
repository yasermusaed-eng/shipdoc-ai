"""
app.py — ShipDoc AI Story-First Landing Page.

A narrative landing page highlighting the operational pain points of shipping
document verification and introducing ShipDoc AI's core capabilities.
"""

import sys
from pathlib import Path
import streamlit as st

# Setup module resolution
PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(DATA_DIR))
sys.path.insert(0, str(SRC_DIR))

from ui_common import init_shared_state, render_sidebar

st.set_page_config(
    page_title="ShipDoc AI — Overview",
    page_icon="🚢",
    layout="wide",
)

# Initialize persistent session state & shared sidebar
init_shared_state()
render_sidebar()

# 1. Hero Section
st.markdown("## 🚨 *“70% of shipping documents are rejected on first presentation — not because paperwork is missing, but because it doesn’t match.”*")
st.caption("— **Source: ICC / UCP 600 global trade surveys.**")
st.markdown("### **ShipDoc AI catches the mismatch before it costs you the shipment.**")

st.divider()

# 2. The Problem Section
st.markdown("### ⚠️ The Problem")
st.markdown(
    "Shipping ops teams spend hours sifting through cluttered inboxes where critical document verification requests "
    "are mixed with invoice questions, booking updates, and spam. Operators must then manually cross-reference two lengthy "
    "documents field-by-field — repeated 3 to 4 times per shipment as drafts circulate. A single overlooked mismatch "
    "triggers carrier amendment penalties, customs delays, and costly cargo release hold-ups."
)

st.divider()

# 3. Where Existing Tools Fall Short Section
st.markdown("### ❌ Where Existing Tools Fall Short")
st.markdown(
    """
* **Built for high-volume standardized docs, not messy inboxes**: Rigid OCR and traditional templates expect pristine layouts and fail when documents arrive in varied carrier formats, differing header terms, or informal email bodies.
* **Long deployment cycles**: Heavy enterprise suites require months of custom implementation and process overhaul, unsuited to how quickly operations teams need adaptable tooling.
* **No built-in escalation when unsure**: When traditional systems encounter ambiguity or poor quality, they either silently guess or do nothing — leaving teams blind to hidden compliance risks.
    """
)

st.divider()

# 4. Introducing ShipDoc AI Section (3 Flagship Feature Cards)
st.markdown("### 💡 Introducing ShipDoc AI")
st.write("An intelligent operations copilot purpose-built for high-velocity shipping documentation workflows.")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        """
        <div style="border: 1px solid rgba(128,128,128,0.25); border-radius: 12px; padding: 20px; min-height: 160px; background-color: rgba(128,128,128,0.04);">
            <div style="font-size: 26px; margin-bottom: 8px;">📬</div>
            <h4 style="margin: 0 0 6px 0;">Inbox Triage</h4>
            <p style="color: #6b7280; font-size: 13px; line-height: 1.5; margin: 0;">
                Automatically filters mixed inbox communications into comparison requests, new SIs, invoice queries, and spam.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        """
        <div style="border: 1px solid rgba(128,128,128,0.25); border-radius: 12px; padding: 20px; min-height: 160px; background-color: rgba(128,128,128,0.04);">
            <div style="font-size: 26px; margin-bottom: 8px;">⚡</div>
            <h4 style="margin: 0 0 6px 0;">Field-Level Reconciliation</h4>
            <p style="color: #6b7280; font-size: 13px; line-height: 1.5; margin: 0;">
                Extracts the 7 canonical shipment fields and deterministically cross-checks SI vs. draft BL with red-highlighted diffs.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col3:
    st.markdown(
        """
        <div style="border: 1px solid rgba(128,128,128,0.25); border-radius: 12px; padding: 20px; min-height: 160px; background-color: rgba(128,128,128,0.04);">
            <div style="font-size: 26px; margin-bottom: 8px;">🛡️</div>
            <h4 style="margin: 0 0 6px 0;">Escalation with Reasoning</h4>
            <p style="color: #6b7280; font-size: 13px; line-height: 1.5; margin: 0;">
                Routes unreadable docs, missing attachments, and low-confidence predictions to human operators with explicit audit logs.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.write("")
st.write("")

# 5. Prominent Enter Dashboard Button
c_left, c_mid, c_right = st.columns([1, 2, 1])
with c_mid:
    if st.button("🚀 Enter Dashboard ➔", type="primary", use_container_width=True):
        st.switch_page("pages/1_Dashboard.py")
