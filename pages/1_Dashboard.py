"""
pages/1_Dashboard.py — Operational Metrics & Pipeline Execution Dashboard.

Contains:
1. One-click "Run pipeline" button to reprocess all emails and persist in session state
2. Operational metric tiles (Total Emails, SI/BL Checks, Mismatches, Escalations)
3. Breakdown of categories and verification outcomes
"""

import json
import sys
from collections import Counter
from pathlib import Path
import pandas as pd
import streamlit as st

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
        st.session_state["results"] = results
    st.success("Pipeline executed successfully! Results refreshed and saved.")
    st.rerun()


col_btn, col_spacer = st.columns([2, 5])
with col_btn:
    if st.button("🔄 Run pipeline", type="primary", use_container_width=True):
        run_pipeline()

results = st.session_state.get("results", [])

if not results:
    st.warning("⚠️ No pipeline results in memory. Click **'Run pipeline'** above to process the dataset.")
else:
    total = len(results)
    comparisons = sum(1 for r in results if r.get("category") == "document_comparison")
    mismatches = sum(1 for r in results if r.get("mismatch_found") is True)
    escalations = sum(1 for r in results if r.get("escalate") is True)
    ok_count = sum(1 for r in results if r.get("mismatch_found") is False)

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    col_m1.metric("Total Emails", total, help="Total emails in inbox dataset")
    col_m2.metric("SI / BL Checks", comparisons, help="Emails requiring SI vs BL document cross-verification")
    col_m3.metric("Mismatches Flagged", mismatches, delta=f"{mismatches/total*100:.1f}%", delta_color="inverse", help="Cases with >= 1 field discrepancy")
    col_m4.metric("Human Escalations", escalations, delta=f"{escalations/total*100:.1f}%", delta_color="inverse", help="Low confidence, missing, or unreadable docs")

    st.divider()

    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("📬 Inbox Category Distribution")
        cat_counts = Counter(r.get("category") for r in results)
        cat_df = pd.DataFrame([
            {"Category": k, "Count": v, "Percentage": f"{v/total*100:.1f}%"}
            for k, v in sorted(cat_counts.items(), key=lambda x: -x[1])
        ])
        st.dataframe(cat_df, use_container_width=True, hide_index=True)
        st.bar_chart(cat_df.set_index("Category")["Count"], color="#1f77b4")

    with col_right:
        st.subheader("🔍 Verification Outcomes (Comparison Requests)")
        outcome_data = {
            "Verified (OK)": ok_count,
            "Mismatch Detected": mismatches,
            "Needs Review (Escalated)": escalations,
        }
        outcome_df = pd.DataFrame([
            {"Status": k, "Count": v}
            for k, v in outcome_data.items()
        ])
        st.dataframe(outcome_df, use_container_width=True, hide_index=True)
        st.bar_chart(outcome_df.set_index("Status")["Count"], color="#ff7f0e")

    st.divider()
    st.info("💡 Go to **2_Inbox_Explorer** to inspect individual email fields and side-by-side document diffs.")
