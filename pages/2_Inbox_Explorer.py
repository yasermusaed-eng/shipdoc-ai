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

# Setup module resolution
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
SRC_DIR = PROJECT_ROOT / "src"
OUTPUT_DIR = PROJECT_ROOT / "output"

sys.path.insert(0, str(DATA_DIR))
sys.path.insert(0, str(SRC_DIR))

from ui_common import init_shared_state, render_sidebar, get_inbox, compute_verification_metrics
from extractor import extract_fields
from comparator import compare_documents, CANONICAL_FIELDS
from pipeline import _find_si_and_bl, _read_doc_text

st.set_page_config(
    page_title="ShipDoc AI — Inbox Explorer",
    page_icon="📋",
    layout="wide",
)

# Initialize persistent session state across pages
init_shared_state()
render_sidebar()

st.title("📋 Inbox Explorer & Document Comparison")
st.caption("Inspect logistics communications, cross-reference SI and BL attachments, and analyze discrepancies")

results = st.session_state.get("results", [])

if not results:
    st.markdown("---")
    st.error(
        "### 💭 No pipeline data loaded yet\n\n"
        "The inbox hasn't been processed. Please go to the **Dashboard** page and click "
        "**'Run pipeline'** to load results — then come back here to explore the inbox."
    )
    st.page_link("pages/1_Dashboard.py", label="Go to Dashboard → Run pipeline", icon="🚀")
    st.stop()

inbox = get_inbox()

# Main 2-column layout
left_col, right_col = st.columns([1, 1])

# Convert results into DataFrame
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

    # Metrics for status options mini-legend
    # NOTE: compute_verification_metrics returns 'total_emails' (not 'total')
    metrics = compute_verification_metrics(results)
    total_emails = metrics["total_emails"]  # explicit local var to prevent future key confusion

    # Dual filter controls: Category and Status
    f_col1, f_col2 = st.columns(2)

    with f_col1:
        cat_filter = st.selectbox(
            "Filter Category",
            ["All", "document_comparison", "invoice_query", "new_si_request", "general", "spam"],
            index=0,
        )

    with f_col2:
        status_options = [
            f"All ({total_emails})",
            f"Verified (OK) ({metrics['verified_ok']})",
            f"Mismatch Detected ({metrics['mismatches']})",
            f"Needs Review (Escalated) ({metrics['escalations']})",
        ]
        status_filter = st.selectbox(
            "Filter Status",
            status_options,
            index=0,
        )

    # 1. Apply category filter
    filtered_df = df if cat_filter == "All" else df[df["category"] == cat_filter]

    # 2. Apply status filter independently
    if status_filter.startswith("Verified (OK)"):
        filtered_df = filtered_df[
            (filtered_df["category"] == "document_comparison")
            & (filtered_df["mismatch_found"] == False)
            & (filtered_df["escalate"] == False)
        ]
    elif status_filter.startswith("Mismatch Detected"):
        filtered_df = filtered_df[filtered_df["mismatch_found"] == True]
    elif status_filter.startswith("Needs Review (Escalated)"):
        filtered_df = filtered_df[filtered_df["escalate"] == True]

    # Email selection dropdown (strictly scoped to filtered_df)
    email_ids = filtered_df["email_id"].tolist()
    if email_ids:
        default_index = 0
        if "email_004" in email_ids:
            default_index = email_ids.index("email_004")

        selected_email_id = st.selectbox(
            f"Select an email record to inspect ({len(email_ids)} available):",
            email_ids,
            index=default_index,
        )
    else:
        st.info("ℹ️ No email records match the selected Category + Status combination.")
        selected_email_id = None

    # Render Table
    st.caption(f"Showing **{len(filtered_df)}** of **{len(df)}** emails")
    st.dataframe(
        filtered_df,
        use_container_width=True,
        height=480,
        hide_index=True,
    )

with right_col:
    if not selected_email_id:
        st.subheader("🔍 Detail Inspection")
        st.info("No email record matches the selected filters. Please adjust the filters on the left.")
        st.stop()

    st.subheader(f"🔍 Detail Inspection: `{selected_email_id}`")

    record = next((r for r in results if r.get("email_id") == selected_email_id), None)
    if not record:
        st.info("Select an email from the left table.")
        st.stop()

    # Raw email metadata
    raw_email = inbox.get(selected_email_id)
    st.markdown(f"**Subject:** {raw_email.get('subject', 'N/A')}")
    st.markdown(f"**From:** `{raw_email.get('from', 'N/A')}`")

    cat = record.get("category")
    is_escalated = record.get("escalate")
    mismatch_found = record.get("mismatch_found")

    # Status Badges
    if is_escalated:
        st.warning(f"⚠️ **STATUS: NEEDS_REVIEW (Escalated)** — {record.get('escalation_reason')}")
    elif mismatch_found is True:
        st.error("🚨 **STATUS: MISMATCH DETECTED** — Discrepancies detected between SI and BL.")
    elif mismatch_found is False:
        st.success("✅ **STATUS: VERIFIED (OK)** — All 7 canonical shipment fields match perfectly.")
    else:
        st.info(f"ℹ️ **Category:** `{cat}` (No document comparison required)")

    # Side-by-side comparison for document_comparison
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

                # Construct comparison table HTML with high-contrast theme-adaptive styling
                rows_html = []
                for f in CANONICAL_FIELDS:
                    s_val = si_fields.get(f) or "*(null)*"
                    b_val = bl_fields.get(f) or "*(null)*"
                    is_diff = f in mismatched_fields

                    if is_diff:
                        row_class = "mismatch-row"
                        tag = '<span style="color: #ef4444; font-weight: 800;">[MISMATCH]</span>'
                    else:
                        row_class = "match-row"
                        tag = '<span style="color: #10b981; font-weight: 800;">[MATCH]</span>'

                    rows_html.append(
                        f"<tr class='{row_class}'>"
                        f"<td><code>{f}</code></td>"
                        f"<td>{s_val}</td>"
                        f"<td>{b_val}</td>"
                        f"<td style='text-align: center;'>{tag}</td>"
                        f"</tr>"
                    )

                table_html = f"""
                <table class='shipdoc-table'>
                    <thead>
                        <tr>
                            <th style='width: 22%;'>Field</th>
                            <th style='width: 35%;'>Shipping Instruction (SI)</th>
                            <th style='width: 35%;'>Bill of Lading (BL)</th>
                            <th style='width: 8%; text-align: center;'>Result</th>
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

        # Raw document attachments expander
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
