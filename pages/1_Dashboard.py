"""
pages/1_Dashboard.py — Operational Metrics & Pipeline Execution Dashboard.

Contains:
1. One-click "Run pipeline" button to reprocess all emails and persist in session state
2. Operational metric tiles:
   - Total Emails
   - SI/BL Checks
   - Mismatches Flagged
   - Human Escalations
   - Estimated manual review time saved (in hours, based on 6 min/comparison benchmark)
3. Direct "View Escalation Queue" button with dynamic pending count badge
4. Triage noise filtering bar chart (document_comparison, new_si_request, invoice_query, general, spam)
5. Breakdown of categories and verification outcomes
"""

import json
import sys
from collections import Counter
from pathlib import Path
import pandas as pd
import streamlit as st

# Setup module resolution
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
SRC_DIR = PROJECT_ROOT / "src"
OUTPUT_DIR = PROJECT_ROOT / "output"
RESULTS_PATH = OUTPUT_DIR / "results.json"
SUBMISSION_PATH = OUTPUT_DIR / "submission.json"

sys.path.insert(0, str(DATA_DIR))
sys.path.insert(0, str(SRC_DIR))

from ui_common import init_shared_state, render_sidebar
from pipeline import run_pipeline_dataset
from format_submission import convert_results_to_submission

st.set_page_config(
    page_title="ShipDoc AI — Dashboard",
    page_icon="📊",
    layout="wide",
)

# Initialize persistent session state across pages
init_shared_state()
render_sidebar()

st.title("📊 Operations Dashboard")
st.caption("Real-time pipeline monitoring, verification metrics, and dataset ingestion")


def run_pipeline():
    with st.spinner("Processing all emails through verification pipeline..."):
        results = run_pipeline_dataset(DATA_DIR, RESULTS_PATH)
        submission = convert_results_to_submission(results)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        with open(SUBMISSION_PATH, "w", encoding="utf-8") as f:
            json.dump(submission, f, indent=2)
        # Update session state to persist across all pages
        st.session_state["results"] = results
    st.success("Pipeline executed successfully! Results refreshed and saved.")
    st.rerun()


results = st.session_state.get("results", [])

# Compute operational counts if results exist
total = len(results) if results else 0
comparisons = sum(1 for r in results if r.get("category") == "document_comparison") if results else 0
mismatches = sum(1 for r in results if r.get("mismatch_found") is True) if results else 0
escalations = sum(1 for r in results if r.get("escalate") is True) if results else 0
ok_count = sum(1 for r in results if r.get("mismatch_found") is False) if results else 0
time_saved_hours = (comparisons * 6) / 60.0 if results else 0.0

# Top Control & Navigation Bar
col_btn1, col_btn2, col_spacer = st.columns([2, 2.5, 4.5])

with col_btn1:
    if st.button("🔄 Run pipeline", type="primary", use_container_width=True):
        run_pipeline()

with col_btn2:
    escalation_label = f"⚠️ View Escalation Queue ({escalations})"
    if st.button(escalation_label, use_container_width=True):
        st.switch_page("pages/3_Escalation_Queue.py")

st.divider()

if not results:
    st.warning("⚠️ No pipeline results in memory. Click **'Run pipeline'** above to process the dataset.")
else:
    # 5 Metric Tiles (including Estimated manual review time saved)
    col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
    
    col_m1.metric(
        "Total Emails", 
        total, 
        help="Total incoming emails processed across the entire inbox dataset"
    )
    col_m2.metric(
        "SI / BL Checks", 
        comparisons, 
        help="Emails classified as document_comparison requiring SI vs. BL reconciliation"
    )
    col_m3.metric(
        "Mismatches Flagged", 
        mismatches, 
        delta=f"{mismatches/total*100:.1f}% of inbox", 
        delta_color="inverse", 
        help="Comparison requests where at least one canonical field differs"
    )
    col_m4.metric(
        "Human Escalations", 
        escalations, 
        delta=f"{escalations/total*100:.1f}% triage rate", 
        delta_color="inverse", 
        help="Cases routed to human operators due to unreadable files, missing attachments, or low confidence"
    )
    col_m5.metric(
        "Est. Review Time Saved", 
        f"{time_saved_hours:.1f} hrs", 
        delta="Automated", 
        help="Computed as: 178 document_comparison emails × 6 minutes assumed manual line-by-line verification time per shipment. (Source: Freight forwarding & logistics operations benchmarks)."
    )

    st.divider()

    # 2. Triage Filtering Bar Chart (Category Noise vs Document Verification)
    st.subheader("📬 Inbox Triage: Filtering Operational Noise")
    st.caption("Visual proof that the triage classification layer filters out non-comparison noise (invoice queries, new SI requests, general notices, spam) before invoking the document extraction and comparison pipeline.")

    expected_categories = [
        "document_comparison",
        "new_si_request",
        "invoice_query",
        "general",
        "spam",
    ]
    raw_cat_counts = Counter(r.get("category") for r in results)
    
    triage_chart_data = pd.DataFrame([
        {"Category": cat, "Email Count": raw_cat_counts.get(cat, 0)}
        for cat in expected_categories
    ])
    
    st.bar_chart(
        triage_chart_data.set_index("Category")["Email Count"], 
        color="#1f77b4",
        height=320,
    )

    st.divider()

    # Additional Detailed Breakdowns
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("📋 Detailed Category Breakdown")
        cat_df = pd.DataFrame([
            {
                "Category": k, 
                "Count": v, 
                "Percentage": f"{v/total*100:.1f}%",
                "Action Taken": "Extract & Cross-Check" if k == "document_comparison" else "Route / Acknowledge"
            }
            for k, v in triage_chart_data.set_index("Category")["Email Count"].items()
        ])
        st.dataframe(cat_df, use_container_width=True, hide_index=True)

    with col_right:
        st.subheader("🔍 Verification Outcomes (Comparison Requests)")
        outcome_data = {
            "Verified (OK)": ok_count,
            "Mismatch Detected": mismatches,
            "Needs Review (Escalated)": escalations,
        }
        outcome_df = pd.DataFrame([
            {"Verification Status": k, "Count": v, "Percentage of Checks": f"{v/comparisons*100:.1f}%"}
            for k, v in outcome_data.items()
        ])
        st.dataframe(outcome_df, use_container_width=True, hide_index=True)
        st.bar_chart(outcome_df.set_index("Verification Status")["Count"], color="#ff7f0e", height=180)

    st.divider()
    st.info("💡 Go to **2_Inbox_Explorer** to inspect individual email fields and side-by-side document diffs, or **3_Escalation_Queue** to review pending triage items.")
