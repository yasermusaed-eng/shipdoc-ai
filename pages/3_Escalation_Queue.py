"""
pages/3_Escalation_Queue.py — Dedicated Human-in-the-Loop Triage & Escalation Interface.

Proves the "Ask for help" capability by isolating cases where the pipeline
safely abstained from guessing and requested human operator review with explicit reasoning.
"""

from datetime import datetime
import sys
from pathlib import Path
import streamlit as st

# Setup module resolution
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(DATA_DIR))
sys.path.insert(0, str(SRC_DIR))

from ui_common import init_shared_state, render_sidebar, get_inbox

st.set_page_config(
    page_title="ShipDoc AI — Escalation Queue",
    page_icon="⚠️",
    layout="wide",
)

# Initialize persistent session state across pages
init_shared_state()
render_sidebar()

# Session-state for mock resolved escalations
if "resolved_escalations" not in st.session_state:
    st.session_state["resolved_escalations"] = {}

inbox = get_inbox()
results = st.session_state.get("results", [])

if not results:
    st.warning("⚠️ No pipeline results in memory. Please visit **1_Dashboard** and click **'Run pipeline'** first.")
    st.stop()

# 1. Filter results to only escalate == true
all_comparison_emails = [r for r in results if r.get("category") == "document_comparison"]
all_escalated = [r for r in results if r.get("escalate") is True]

total_comparisons = len(all_comparison_emails)
total_escalated = len(all_escalated)
resolved_ids = set(st.session_state["resolved_escalations"].keys())
pending_escalations = [r for r in all_escalated if r["email_id"] not in resolved_ids]

# 4. Top One-Line Summary
st.title("⚠️ Human-in-the-Loop Escalation Queue")
pct_escalated = (total_escalated / total_comparisons * 100) if total_comparisons else 0
st.markdown(
    f"### 🛡️ **{total_escalated} of {total_comparisons} document-comparison emails required human review ({pct_escalated:.1f}%).**"
)
st.caption(
    "To preserve total auditability, ShipDoc AI never silently guesses when attachments are missing, "
    "files are unreadable, or extraction confidence is low. It halts autonomous execution and surfaces "
    "the case here with an explicit, traceable reason."
)

st.divider()

# Quick Status Bar & Reason Filter
col_stat1, col_stat2, col_stat3, col_filter = st.columns([1.5, 1.5, 1.5, 3.5])
col_stat1.metric("Total Escalations", total_escalated)
col_stat2.metric("Pending Review", len(pending_escalations), delta=f"-{len(resolved_ids)} resolved" if resolved_ids else None)
col_stat3.metric("Resolved in Session", len(resolved_ids))

with col_filter:
    reason_filter = st.selectbox(
        "Filter by Escalation Reason Category:",
        ["All Reasons", "Missing Attachment", "Unreadable File Format", "Missing Field Values (High Nulls)", "Low Confidence"],
        index=0,
    )

def _matches_filter(reason_text: str, filter_choice: str) -> bool:
    if filter_choice == "All Reasons":
        return True
    r = (reason_text or "").lower()
    if filter_choice == "Missing Attachment":
        return "missing_attachment" in r or "missing si" in r or "missing bl" in r
    if filter_choice == "Unreadable File Format":
        return "unreadable" in r or "empty_document" in r or ".xlsx" in r or ".pdf" in r or "binary" in r
    if filter_choice == "Missing Field Values (High Nulls)":
        return "missing_value" in r or "null fields" in r
    if filter_choice == "Low Confidence":
        return "low_confidence" in r or "confidence" in r
    return True

filtered_pending = [
    r for r in pending_escalations
    if _matches_filter(r.get("escalation_reason", ""), reason_filter)
]

# Pagination Controls
items_per_page = 10
total_items = len(filtered_pending)
total_pages = max(1, (total_items + items_per_page - 1) // items_per_page)

col_page_info, col_page_num = st.columns([4, 2])
with col_page_info:
    st.write(f"Showing **{min(total_items, 1)}–{min(total_items, items_per_page)}** of **{total_items}** pending cases")
with col_page_num:
    page = st.number_input("Page", min_value=1, max_value=total_pages, value=1, step=1)

start_idx = (page - 1) * items_per_page
end_idx = min(start_idx + items_per_page, total_items)
displayed_items = filtered_pending[start_idx:end_idx]

st.markdown("---")

# 2. Render Each Escalated Email as a Prominent Card
if not displayed_items:
    st.success("🎉 No pending escalation cases matching this filter! All items resolved.")
else:
    for item in displayed_items:
        eid = item.get("email_id")
        reason = item.get("escalation_reason", "No reason specified")
        
        # Fetch original email metadata
        raw_email = inbox.get(eid) if inbox else {}
        subject = raw_email.get("subject", "(No Subject)")
        sender = raw_email.get("from", "(Unknown Sender)")
        attachments = raw_email.get("attachments", []) or []

        # Determine badge color and label
        badge_label = "ESCALATION"
        if "missing_attachment" in reason.lower():
            badge_label = "MISSING ATTACHMENT"
        elif "unreadable" in reason.lower():
            badge_label = "UNREADABLE FORMAT"
        elif "missing_value" in reason.lower():
            badge_label = "HIGH NULL COUNT"
        elif "low_confidence" in reason.lower():
            badge_label = "LOW CONFIDENCE"

        # Card Container
        with st.container():
            st.markdown(
                f"""
                <div style="border: 1px solid rgba(245, 158, 11, 0.4); border-radius: 12px; padding: 18px; margin-bottom: 16px; background-color: rgba(245, 158, 11, 0.03);">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <span style="font-family: monospace; font-size: 14px; font-weight: bold; background-color: rgba(128,128,128,0.15); padding: 3px 8px; border-radius: 6px;">
                            {eid}
                        </span>
                        <span style="background-color: #f59e0b; color: #ffffff; font-size: 11px; font-weight: 700; padding: 3px 10px; border-radius: 9999px; letter-spacing: 0.5px;">
                            {badge_label}
                        </span>
                    </div>
                    <div style="font-size: 15px; font-weight: 700; color: inherit; margin-bottom: 4px;">
                        {subject}
                    </div>
                    <div style="font-size: 12px; color: #6b7280; margin-bottom: 12px;">
                        From: <code style="color: inherit;">{sender}</code> &nbsp;•&nbsp; Attachments: <code>{', '.join(attachments) if attachments else 'None'}</code>
                    </div>
                    <!-- PROMINENT ESCALATION CALLOUT BOX -->
                    <div style="background-color: #fffbeb; border-left: 5px solid #d97706; padding: 12px 14px; border-radius: 6px; margin: 10px 0;">
                        <div style="color: #92400e; font-weight: 700; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 3px;">
                            ⚠️ Explicit Escalation Trigger / Reason:
                        </div>
                        <div style="color: #78350f; font-family: monospace; font-size: 13px; font-weight: 600; line-height: 1.4;">
                            {reason}
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # 3. Mock Resolve Action Panel
            col_exp, col_note, col_action = st.columns([2, 4, 1.5])
            
            with col_exp:
                with st.expander("📄 View Email Content"):
                    st.text(raw_email.get("body", "(Empty body)"))
            
            with col_note:
                reviewer_note = st.text_input(
                    "Operator Resolution Note:",
                    placeholder="e.g. Contacted freight forwarder for revised BL copy...",
                    key=f"input_note_{eid}",
                    label_visibility="collapsed",
                )

            with col_action:
                if st.button("✅ Resolve", key=f"btn_resolve_{eid}", type="primary", use_container_width=True):
                    st.session_state["resolved_escalations"][eid] = {
                        "subject": subject,
                        "reason": reason,
                        "note": reviewer_note.strip() or "Reviewed and verified manually by operator.",
                        "resolved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    }
                    st.toast(f"Case {eid} moved to Resolved Archive!", icon="✅")
                    st.rerun()

            st.write("")

# 3b. Resolved Cases Section Below
if st.session_state["resolved_escalations"]:
    st.divider()
    st.subheader(f"✅ Resolved Cases Archive ({len(st.session_state['resolved_escalations'])})")
    st.caption("Cases successfully reviewed and cleared during this operator session.")

    for res_id, res_info in st.session_state["resolved_escalations"].items():
        with st.expander(f"✅ {res_id}: {res_info.get('subject')} (Resolved at {res_info.get('resolved_at')})"):
            st.markdown(f"**Escalation Trigger:** `{res_info.get('reason')}`")
            st.markdown(f"**Operator Reviewer Note:** *\"{res_info.get('note')}\"*")
