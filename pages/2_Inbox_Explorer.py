"""
pages/2_Inbox_Explorer.py — Interactive Inbox Explorer and Side-by-Side Comparison.

Contains:
1. Filterable email table (email_id, category, mismatch_found, escalate)
2. Interactive email selection and inspector panel
3. Side-by-side 7-field SI vs BL comparison with red mismatch highlighting
4. Raw attachment and email body viewers
"""

import sys
from pathlib import Path
import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
SRC_DIR = PROJECT_ROOT / "src"
OUTPUT_DIR = PROJECT_ROOT / "output"

sys.path.insert(0, str(DATA_DIR))
sys.path.insert(0, str(SRC_DIR))

from ui_common import init_shared_state, render_sidebar, get_inbox
from extractor import extract_fields
from comparator import compare_documents, CANONICAL_FIELDS
from pipeline import _find_si_and_bl, _read_doc_text

st.set_page_config(
    page_title="ShipDoc AI — Inbox Explorer",
    page_icon="📋",
    layout="wide",
)

init_shared_state()
render_sidebar()

st.title("📋 Inbox Explorer & Document Comparison")
st.caption("Inspect logistics communications, cross-reference SI and BL attachments, and analyze discrepancies")

results = st.session_state.get("results", [])

if not results:
    st.warning("⚠️ No pipeline results in memory. Please visit **1_Dashboard** and click **'Run pipeline'** first.")
    st.stop()

inbox = get_inbox()

left_col, right_col = st.columns([1, 1])

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
    st.subheader("📬 Filter Inbox Records")

    cat_filter = st.selectbox(
        "Filter Category",
        ["All", "document_comparison", "invoice_query", "new_si_request", "general", "spam"],
        index=0,
    )

    filtered_df = df if cat_filter == "All" else df[df["category"] == cat_filter]

    email_ids = filtered_df["email_id"].tolist()
    default_index = 0
    if "email_004" in email_ids:
        default_index = email_ids.index("email_004")

    selected_email_id = st.selectbox(
        "Select an email record to inspect:",
        email_ids,
        index=default_index if email_ids else 0,
    )

    st.dataframe(
        filtered_df,
        use_container_width=True,
        height=520,
        hide_index=True,
    )

with right_col:
    st.subheader(f"🔍 Detail Inspection: `{selected_email_id}`")

    record = next((r for r in results if r.get("email_id") == selected_email_id), None)
    if not record:
        st.info("Select an email from the left table.")
        st.stop()

    raw_email = inbox.get(selected_email_id)
    st.markdown(f"**Subject:** {raw_email.get('subject', 'N/A')}")
    st.markdown(f"**From:** `{raw_email.get('from', 'N/A')}`")

    cat = record.get("category")
    is_escalated = record.get("escalate")
    mismatch_found = record.get("mismatch_found")

    if is_escalated:
        st.warning(f"⚠️ **STATUS: NEEDS_REVIEW (Escalated)** — {record.get('escalation_reason')}")
    elif mismatch_found is True:
        st.error("🚨 **STATUS: MISMATCH DETECTED** — Discrepancies detected between SI and BL.")
    elif mismatch_found is False:
        st.success("✅ **STATUS: VERIFIED (OK)** — All 7 canonical shipment fields match perfectly.")
    else:
        st.info(f"ℹ️ **Category:** `{cat}` (No document comparison required)")

    if cat == "document_comparison":
        st.markdown("#### Side-by-Side 7-Field Comparison (SI vs. BL)")

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

        with st.expander("📄 View Raw Document Attachments"):
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
        with st.expander("✉️ View Raw Email Body", expanded=True):
            st.text(raw_email.get("body", "(Empty body)"))
