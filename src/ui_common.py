"""
ui_common.py — Shared utilities, session state persistence, theme management, and sidebar navigation branding.
"""

from datetime import datetime
import json
import sys
from pathlib import Path
import streamlit as st

# Setup project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
SRC_DIR = PROJECT_ROOT / "src"
OUTPUT_DIR = PROJECT_ROOT / "output"
RESULTS_PATH = OUTPUT_DIR / "results.json"
SUBMISSION_PATH = OUTPUT_DIR / "submission.json"

sys.path.insert(0, str(DATA_DIR))
sys.path.insert(0, str(SRC_DIR))

try:
    from loader import Inbox
except ImportError:
    from data.loader import Inbox


def get_inbox():
    """Returns singleton-like Inbox instance for dataset reading."""
    return Inbox(str(DATA_DIR))


def init_shared_state():
    """Initializes and persists pipeline results and run timestamps across Streamlit pages."""
    # 1. Persist results dataframe / dict across all page transitions
    if "results" not in st.session_state or st.session_state["results"] is None:
        if RESULTS_PATH.exists():
            try:
                with open(RESULTS_PATH, "r", encoding="utf-8") as f:
                    st.session_state["results"] = json.load(f)
            except Exception:
                st.session_state["results"] = []
        else:
            st.session_state["results"] = []

    # 2. Persist last pipeline run timestamp
    if "last_run_timestamp" not in st.session_state or not st.session_state["last_run_timestamp"]:
        if RESULTS_PATH.exists():
            mtime = RESULTS_PATH.stat().st_mtime
            st.session_state["last_run_timestamp"] = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
        else:
            st.session_state["last_run_timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def apply_custom_theme():
    """
    Injects universal CSS rules to ensure flawless rendering across both Light and Dark modes.
    Specifically fixes table header contrast and unifies red/pink (mismatch/escalate)
    and green (match/resolved) semantics.
    """
    st.markdown(
        """
        <style>
        /* Universal table styling compatible with both Light & Dark themes */
        table.shipdoc-table {
            width: 100%;
            border-collapse: collapse;
            font-family: inherit;
            font-size: 13px;
            margin: 10px 0;
            border: 1px solid rgba(128, 128, 128, 0.25);
            border-radius: 8px;
            overflow: hidden;
        }
        table.shipdoc-table th {
            padding: 10px 12px;
            background-color: rgba(128, 128, 128, 0.18) !important;
            color: inherit !important;
            font-weight: 700;
            border-bottom: 2px solid rgba(128, 128, 128, 0.35);
            text-align: left;
        }
        table.shipdoc-table td {
            padding: 10px 12px;
            border-bottom: 1px solid rgba(128, 128, 128, 0.15);
            color: inherit !important;
        }
        table.shipdoc-table tr.mismatch-row {
            background-color: rgba(239, 68, 68, 0.16) !important;
            border-left: 5px solid #ef4444 !important;
        }
        table.shipdoc-table tr.match-row {
            background-color: transparent !important;
        }
        table.shipdoc-table tr.match-row:hover {
            background-color: rgba(128, 128, 128, 0.08) !important;
        }

        /* Color Scheme Classes */
        .color-mismatch {
            color: #ef4444 !important;
            font-weight: 700;
        }
        .color-match {
            color: #10b981 !important;
            font-weight: 700;
        }
        .color-escalate {
            color: #f59e0b !important;
            font-weight: 700;
        }

        /* Badges */
        .badge-mismatch {
            color: #ef4444 !important;
            background-color: rgba(239, 68, 68, 0.15);
            border: 1px solid rgba(239, 68, 68, 0.4);
            padding: 3px 8px;
            border-radius: 6px;
            font-weight: 700;
            font-size: 11px;
        }
        .badge-match {
            color: #10b981 !important;
            background-color: rgba(16, 185, 129, 0.15);
            border: 1px solid rgba(16, 185, 129, 0.4);
            padding: 3px 8px;
            border-radius: 6px;
            font-weight: 700;
            font-size: 11px;
        }
        .badge-escalate {
            color: #f59e0b !important;
            background-color: rgba(245, 158, 11, 0.15);
            border: 1px solid rgba(245, 158, 11, 0.4);
            padding: 3px 8px;
            border-radius: 6px;
            font-weight: 700;
            font-size: 11px;
        }

        /* Clean Sidebar Navigation styling */
        [data-testid="stSidebarNav"] a span {
            font-weight: 500;
            font-size: 14px;
        }
        </style>

        <script>
        // Clean navigation label: ensure "app" is presented cleanly as "Home"
        function cleanSidebarLabels() {
            try {
                const navLinks = window.parent.document.querySelectorAll('[data-testid="stSidebarNav"] a span');
                navLinks.forEach(el => {
                    if (el.innerText.trim().toLowerCase() === 'app') {
                        el.innerText = 'Home';
                    }
                });
            } catch (e) {}
        }
        cleanSidebarLabels();
        setTimeout(cleanSidebarLabels, 300);
        setTimeout(cleanSidebarLabels, 1000);
        </script>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar():
    """Renders the consistent logo, title, persistent timestamp, and dataset status across all pages."""
    apply_custom_theme()

    st.sidebar.markdown("## 🚢 ShipDoc AI")
    st.sidebar.caption("Shipping Document Verification System  \n**Averis × Monash Hackathon 2026**")
    st.sidebar.divider()

    # Persistent Pipeline Run Timestamp
    last_run = st.session_state.get("last_run_timestamp", "Active")
    st.sidebar.markdown(f"🕒 **Last Pipeline Run:**  \n`{last_run}`")
    st.sidebar.divider()

    results = st.session_state.get("results", [])
    if results:
        total = len(results)
        mismatches = sum(1 for r in results if r.get("mismatch_found") is True)
        escalated = sum(1 for r in results if r.get("escalate") is True)
        
        st.sidebar.markdown(f"**Dataset Status:**  \n`{total}` emails loaded")
        st.sidebar.markdown(f"- 🚨 <span class='color-mismatch'>Mismatches: {mismatches}</span>", unsafe_allow_html=True)
        st.sidebar.markdown(f"- ⚠️ <span class='color-escalate'>Escalations: {escalated}</span>", unsafe_allow_html=True)
        st.sidebar.markdown(f"- ✅ <span class='color-match'>Verified OK: {total - mismatches - escalated}</span>", unsafe_allow_html=True)
    else:
        st.sidebar.info("No pipeline results in memory. Visit **Dashboard** to run the pipeline.")

    st.sidebar.divider()
    st.sidebar.caption("Prototype built for Averis ops team demo.")
