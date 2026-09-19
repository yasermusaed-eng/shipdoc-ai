"""
app.py — Minimal, functional Streamlit UI for Shipping Operations Document Verification.

Built for quick demo screen-recording:
1. Table of processed emails (email_id, category, mismatch_found, escalate)
2. Interactive row inspection with SI vs. BL side-by-side field comparison (mismatches highlighted in red)
3. One-click "Run pipeline" button to reprocess all emails and refresh results
"""

import json
import sys
from pathlib import Path
import pandas as pd
import streamlit as st

# Setup module resolution
PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
SRC_DIR = PROJECT_ROOT / "src"
OUTPUT_DIR = PROJECT_ROOT / "output"
RESULTS_PATH = OUTPUT_DIR / "results.json"

sys.path.insert(0, str(DATA_DIR))
sys.path.insert(0, str(SRC_DIR))

try:
    from loader import Inbox
except ImportError:
    from data.loader import Inbox

from extractor import extract_fields
from comparator import compare_documents, CANONICAL_FIELDS
from pipeline import run_pipeline_dataset, _find_si_and_bl, _read_doc_text
from format_submission import convert_results_to_submission

st.set_page_config(page_title="ShipDoc AI — Verification System", layout="wide")


def load_results():
    if RESULTS_PATH.exists():
        with open(RESULTS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def run_pipeline():
    with st.spinner("Processing all emails through verification pipeline..."):
        results = run_pipeline_dataset(DATA_DIR, RESULTS_PATH)
        submission = convert_results_to_submission(results)
        with open(OUTPUT_DIR / "submission.json", "w", encoding="utf-8") as f:
            json.dump(submission, f, indent=2)
    st.success("Pipeline executed successfully! Results refreshed.")
    st.rerun()


def main():
    st.title("\U0001f6a2 Shipping Document Verification System (ShipDoc AI)")
    st.caption("Averis \u00d7 Monash Hackathon 2026 \u2014 Automated SI vs. BL Discrepancy Detection & Escalation")

    # Top Control Bar
    col_btn, col_metric1, col_metric2, col_metric3, col_metric4 = st.columns([2, 1, 1, 1, 1])

    with col_btn:
        if st.button("\U0001f504 Run pipeline", type="primary", use_container_width=True):
            run_pipeline()

    results = load_results()
    inbox = Inbox(str(DATA_DIR))

    if not results:
        st.warning("No processed results found. Click 'Run pipeline' above to process the dataset.")
        return

    # Metrics
    total = len(results)
    comparisons = sum(1 for r in results if r["category"] == "document_comparison")
    mismatches = sum(1 for r in results if r["mismatch_found"] is True)
    escalations = sum(1 for r in results if r["escalate"] is True)

    col_metric1.metric("Total Emails", total)
    col_metric2.metric("SI/BL Checks", comparisons)
    col_metric3.metric("Mismatches", mismatches)
    col_metric4.metric("Escalated", escalations)

    st.divider()

    # Main layout: Left column table, Right column side-by-side comparison
    left_col, right_col = st.columns([1, 1])

    # Convert results into a Pandas DataFrame
    df = pd.DataFrame([
        {
            "email_id": r.get("email_id"),
            "category": r.get("category"),
            "mismatch_found": r.get("mismatch_found"),
            "escalate": r.get("escalate"),
        }
        for r in results
    ])

    with left_col:
        st.subheader("\U0001f4cb Processed Inbox Emails")

        # Category filter for easy navigation during demo
        cat_filter = st.selectbox(
            "Filter Category",
            ["All", "document_comparison", "invoice_query", "new_si_request", "general", "spam"],
            index=0
        )

        filtered_df = df if cat_filter == "All" else df[df["category"] == cat_filter]

        # Email selection dropdown
        email_ids = filtered_df["email_id"].tolist()
        default_index = 0
        if "email_004" in email_ids:
            default_index = email_ids.index("email_004")

        selected_email_id = st.selectbox(
            "Click/Select an email row to inspect:",
            email_ids,
            index=default_index if email_ids else 0,
        )

        # Render Table
        st.dataframe(
            filtered_df,
            use_container_width=True,
            height=480,
            hide_index=True,
        )

    with right_col:
        st.subheader(f"\U0001f50d Inspection: `{selected_email_id}`")

        # Find result record
        record = next((r for r in results if r.get("email_id") == selected_email_id), None)
        if not record:
            st.info("Select an email from the left table.")
            return

        # Fetch original email content
        raw_email = inbox.get(selected_email_id)
        st.markdown(f"**Subject:** {raw_email.get('subject', 'N/A')}")
        st.markdown(f"**From:** `{raw_email.get('from', 'N/A')}`")

        cat = record.get("category")
        is_escalated = record.get("escalate")
        mismatch_found = record.get("mismatch_found")

        # Status badge
        if is_escalated:
            st.warning(f"\u26a0\ufe0f **STATUS: NEEDS_REVIEW (Escalated)** \u2014 {record.get('escalation_reason')}")
        elif mismatch_found is True:
            st.error("\U0001f6a8 **STATUS: MISMATCH DETECTED** \u2014 One or more shipment fields differ between SI and BL.")
        elif mismatch_found is False:
            st.success("\u2705 **STATUS: VERIFIED (OK)** \u2014 No mismatch detected. All 7 fields match.")
        else:
            st.info(f"\u2139\ufe0f **Category:** `{cat}` (No document comparison required)")

        # Side-by-side comparison for document_comparison
        if cat == "document_comparison":
            st.markdown("#### Side-by-Side Field Comparison (SI vs. BL)")

            attachments = raw_email.get("attachments", []) or []
            si_path, bl_path = _find_si_and_bl(attachments)

            if not si_path or not bl_path:
                st.error("Missing SI or BL attachment for comparison.")
            else:
                si_text, _ = _read_doc_text(inbox, si_path)
                bl_text, _ = _read_doc_text(inbox, bl_path)

                if si_text and bl_text:
                    si_fields = extract_fields(si_text)
                    bl_fields = extract_fields(bl_text)
                    comp_res = compare_documents(si_fields, bl_fields)
                    mismatched_fields = {m["field"] for m in comp_res.get("mismatches", [])}

                    rows_html = []
                    for f in CANONICAL_FIELDS:
                        s_val = si_fields.get(f) or "*(null)*"
                        b_val = bl_fields.get(f) or "*(null)*"
                        is_diff = f in mismatched_fields

                        if is_diff:
                            row_style = "background-color: #ffebee; border-left: 4px solid #d32f2f; font-weight: bold; color: #b71c1c;"
                            tag = '<span style="color: #d32f2f; font-weight: bold;">[MISMATCH]</span>'
                        else:
                            row_style = "border-bottom: 1px solid #e0e0e0;"
                            tag = '<span style="color: #2e7d32;">[MATCH]</span>'

                        rows_html.append(
                            f"<tr style='{row_style}'>"
                            f"<td style='padding: 8px;'><code>{f}</code></td>"
                            f"<td style='padding: 8px;'>{s_val}</td>"
                            f"<td style='padding: 8px;'>{b_val}</td>"
                            f"<td style='padding: 8px; text-align: center;'>{tag}</td>"
                            f"</tr>"
                        )

                    table_html = f"""
                    <table style='width: 100%; border-collapse: collapse; font-family: sans-serif; font-size: 13px;'>
                        <thead>
                            <tr style='background-color: #f5f5f5; border-bottom: 2px solid #ccc; text-align: left;'>
                                <th style='padding: 8px;'>Field</th>
                                <th style='padding: 8px;'>Shipping Instruction (SI)</th>
                                <th style='padding: 8px;'>Bill of Lading (BL)</th>
                                <th style='padding: 8px; text-align: center;'>Result</th>
                            </tr>
                        </thead>
                        <tbody>
                            {''.join(rows_html)}
                        </tbody>
                    </table>
                    """
                    st.html(table_html)
                else:
                    st.info("One or both document contents could not be read as text.")

            with st.expander("\U0001f4c4 View Raw Document Attachments"):
                col_si, col_bl = st.columns(2)
                with col_si:
                    st.caption(f"SI Attachment: `{si_path}`")
                    if si_path:
                        st.code(inbox.read_text(si_path) if si_path.endswith('.txt') else '(binary file)')
                with col_bl:
                    st.caption(f"BL Attachment: `{bl_path}`")
                    if bl_path:
                        st.code(inbox.read_text(bl_path) if bl_path.endswith('.txt') else '(binary file)')
        else:
            with st.expander("\u2709\ufe0f View Raw Email Body", expanded=True):
                st.text(raw_email.get("body", "(Empty body)"))


if __name__ == "__main__":
    main()
