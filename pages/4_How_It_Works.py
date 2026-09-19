"""
pages/4_How_It_Works.py — Visual Pipeline Architecture & Technical Design Overview.

Provides a 30-second technical overview for hackathon judges:
1. Horizontal step diagram (Inbox -> Classify -> Extract -> Compare -> Escalate/Report)
2. The engineering "why" behind each architectural decision
3. Tech stack badges and component breakdown
4. Honest "Known Limitations" scope boundary disclosure
"""

import sys
from pathlib import Path
import streamlit as st

# Setup module resolution
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

# Initialize persistent session state across pages
init_shared_state()
render_sidebar()

st.title("💡 How It Works: Pipeline Architecture")
st.caption("A 30-second technical breakdown of our hybrid LLM + deterministic verification engine")

st.divider()

# 1. Horizontal Step Diagram (Visual SVG Flowchart)
st.subheader("🔄 End-to-End Pipeline Flow")

diagram_html = """
<div style="width: 100%; overflow-x: auto; padding: 15px 0;">
  <div style="display: flex; align-items: center; justify-content: space-between; min-width: 900px; gap: 8px;">
    
    <!-- Step 1 -->
    <div style="flex: 1; border: 1px solid rgba(128,128,128,0.25); background: rgba(128,128,128,0.05); border-radius: 10px; padding: 14px; text-align: center;">
      <div style="font-size: 24px;">📥</div>
      <div style="font-weight: 700; font-size: 13px; margin: 4px 0;">1. Inbox Ingestion</div>
      <div style="font-size: 11px; opacity: 0.8;">Raw emails & attachments</div>
    </div>

    <div style="font-size: 18px; color: #9ca3af; font-weight: bold;">➔</div>

    <!-- Step 2 -->
    <div style="flex: 1; border: 1px solid #3b82f6; background: rgba(59, 130, 246, 0.08); border-radius: 10px; padding: 14px; text-align: center;">
      <div style="font-size: 24px;">🏷️</div>
      <div style="font-weight: 700; font-size: 13px; margin: 4px 0; color: #2563eb;">2. Triage & Classify</div>
      <div style="font-size: 11px; opacity: 0.8;">Filter 5 categories</div>
    </div>

    <div style="font-size: 18px; color: #9ca3af; font-weight: bold;">➔</div>

    <!-- Step 3 -->
    <div style="flex: 1; border: 1px solid #8b5cf6; background: rgba(139, 92, 246, 0.08); border-radius: 10px; padding: 14px; text-align: center;">
      <div style="font-size: 24px;">📑</div>
      <div style="font-weight: 700; font-size: 13px; margin: 4px 0; color: #7c3aed;">3. Field Extraction</div>
      <div style="font-size: 11px; opacity: 0.8;">7 canonical fields (SI & BL)</div>
    </div>

    <div style="font-size: 18px; color: #9ca3af; font-weight: bold;">➔</div>

    <!-- Step 4 -->
    <div style="flex: 1; border: 1px solid #10b981; background: rgba(16, 185, 129, 0.08); border-radius: 10px; padding: 14px; text-align: center;">
      <div style="font-size: 24px;">⚖️</div>
      <div style="font-weight: 700; font-size: 13px; margin: 4px 0; color: #059669;">4. Deterministic Compare</div>
      <div style="font-size: 11px; opacity: 0.8;">Zero LLM hallucination</div>
    </div>

    <div style="font-size: 18px; color: #9ca3af; font-weight: bold;">➔</div>

    <!-- Step 5 -->
    <div style="flex: 1; border: 1px solid #f59e0b; background: rgba(245, 158, 11, 0.08); border-radius: 10px; padding: 14px; text-align: center;">
      <div style="font-size: 24px;">🛡️</div>
      <div style="font-weight: 700; font-size: 13px; margin: 4px 0; color: #d97706;">5. Escalate or Report</div>
      <div style="font-size: 11px; opacity: 0.8;">Flag diffs or ask for help</div>
    </div>

  </div>
</div>
"""
st.html(diagram_html)

st.write("")

# 2. Under Each Step: The Engineering "Why"
st.subheader("🎯 Architectural Rationale: Why This Design?")

col_w1, col_w2, col_w3, col_w4, col_w5 = st.columns(5)

with col_w1:
    st.markdown("**📥 Ingestion**")
    st.caption(
        "Ingests messy real-world inboxes containing mixed threads, varied attachments (.txt, .pdf, .xlsx), "
        "and unlabelled customer messages without rigid schema assumptions."
    )

with col_w2:
    st.markdown("**🏷️ Classification**")
    st.caption(
        "Filters out ~65% of noise (invoices, new SIs, general updates, spam) before triggering expensive document extraction, "
        "saving significant compute cost and model latency."
    )

with col_w3:
    st.markdown("**📑 Structured Extraction**")
    st.caption(
        "Leverages LLMs strictly where they excel: mapping chaotic industry jargon ('Port of Loading' vs. 'POL' vs. 'Load Port') "
        "into 7 canonical JSON keys with null-fallback guarantees."
    )

with col_w4:
    st.markdown("**⚖️ Deterministic Compare**")
    st.caption(
        "Deterministic string and numeric matching only — zero LLM judgment on the actual mismatch decision, "
        "guaranteeing auditability and eliminating hallucinations on core compliance logic."
    )

with col_w5:
    st.markdown("**🛡️ Escalate or Report**")
    st.caption(
        "Safety guardrails: halts and escalates unreadable files, missing attachments, or low confidence to human operators "
        "with explicit audit reasons rather than silently failing."
    )

st.divider()

# 3. Tech Stack Row of Badges & Components
st.subheader("🛠️ Technology Stack")

col_t1, col_t2, col_t3, col_t4 = st.columns(4)

with col_t1:
    st.markdown("""
    <div style="border: 1px solid rgba(128,128,128,0.25); border-radius: 8px; padding: 12px; background: rgba(128,128,128,0.03);">
        <div style="font-size: 20px;">🧠</div>
        <div style="font-weight: 700; font-size: 13px; margin-top: 4px;">LLM Intelligence</div>
        <div style="font-size: 12px; opacity: 0.8; margin-top: 2px;">Google Gemini 2.5 Flash</div>
        <div style="font-size: 11px; opacity: 0.65;">(Structured JSON schema output + OpenAI fallback)</div>
    </div>
    """, unsafe_allow_html=True)

with col_t2:
    st.markdown("""
    <div style="border: 1px solid rgba(128,128,128,0.25); border-radius: 8px; padding: 12px; background: rgba(128,128,128,0.03);">
        <div style="font-size: 20px;">🖥️</div>
        <div style="font-weight: 700; font-size: 13px; margin-top: 4px;">Frontend Dashboard</div>
        <div style="font-size: 12px; opacity: 0.8; margin-top: 2px;">Streamlit 1.55</div>
        <div style="font-size: 11px; opacity: 0.65;">Native multipage architecture & session-state persistence</div>
    </div>
    """, unsafe_allow_html=True)

with col_t3:
    st.markdown("""
    <div style="border: 1px solid rgba(128,128,128,0.25); border-radius: 8px; padding: 12px; background: rgba(128,128,128,0.03);">
        <div style="font-size: 20px;">⚙️</div>
        <div style="font-weight: 700; font-size: 13px; margin-top: 4px;">Core Logic Engine</div>
        <div style="font-size: 12px; opacity: 0.8; margin-top: 2px;">Python 3.12 Standard Library</div>
        <div style="font-size: 11px; opacity: 0.65;">Auditable rule-based comparison + regex offline fallback</div>
    </div>
    """, unsafe_allow_html=True)

with col_t4:
    st.markdown("""
    <div style="border: 1px solid rgba(128,128,128,0.25); border-radius: 8px; padding: 12px; background: rgba(128,128,128,0.03);">
        <div style="font-size: 20px;">📦</div>
        <div style="font-weight: 700; font-size: 13px; margin-top: 4px;">Deployment & Evaluation</div>
        <div style="font-size: 12px; opacity: 0.8; margin-top: 2px;">Docker & Git SCM</div>
        <div style="font-size: 11px; opacity: 0.65;">Scoreboard submission API & containerized grading</div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# 4. Known Limitations Expander (Honest Scope Boundary Disclosure)
with st.expander("🔍 Known Limitations & Scope Boundaries (Roadmap)", expanded=False):
    st.markdown("""
We deliberately scope our prototype to proven, reproducible capabilities rather than overpromising. The following real-world complexities are identified as next-stage engineering milestones:

1. **Complex Binary & Multi-tab Documents (.xlsx, .pdf, .docx)**:
   - *Current Behavior*: Safely escalated to `NEEDS_REVIEW` under the `unreadable` reason code.
   - *Next Stage*: Embed `pypdf`, `openpyxl`, and `python-docx` for native tabular cell extraction.

2. **OCR for Physical Scanned Copies & Image Attachments**:
   - *Current Behavior*: Binary scanned images without OCR layers cannot be parsed and trigger escalation.
   - *Next Stage*: Introduce an upstream OCR preprocessing pipeline (Tesseract / Vision LLM) to digitize camera scans and low-DPI faxes.

3. **Handwritten Notes & Physical Endorsement Stamps**:
   - *Current Behavior*: Negotiable Bill of Lading endorsements made by hand are bypassed in text-mode.
   - *Next Stage*: Multimodal region-based visual inspection for endorsement verification.

4. **Adversarial / Corrupted File Recovery**:
   - *Current Behavior*: Corrupted encodings or empty files escalate immediately to human review.
   - *Next Stage*: Automated carrier auto-reply asking for re-transmission of corrupted attachments.
""")

st.caption("ShipDoc AI — Averis × Monash Hackathon 2026")
