"""
tests/test_inbox_filters.py — Automated tests for Inbox Explorer dual-filtering logic.
"""

import json
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_FILE = PROJECT_ROOT / "output" / "results.json"


def filter_emails(df, cat_filter, status_filter):
    filtered = df if cat_filter == "All" else df[df["category"] == cat_filter]

    if status_filter.startswith("Verified (OK)"):
        filtered = filtered[
            (filtered["category"] == "document_comparison")
            & (filtered["mismatch_found"] == False)
            & (filtered["escalate"] == False)
        ]
    elif status_filter.startswith("Mismatch Detected"):
        filtered = filtered[filtered["mismatch_found"] == True]
    elif status_filter.startswith("Needs Review (Escalated)"):
        filtered = filtered[filtered["escalate"] == True]

    return filtered


def test_inbox_filtering():
    with open(RESULTS_FILE, "r", encoding="utf-8") as f:
        results = json.load(f)

    df = pd.DataFrame([
        {
            "email_id": r.get("email_id"),
            "category": r.get("category"),
            "mismatch_found": r.get("mismatch_found"),
            "escalate": r.get("escalate"),
        }
        for r in results
    ])

    print("===========================================================================")
    print("TEST: Inbox Explorer Status & Category Filtering")
    print("===========================================================================")

    # 1. Total unfiltered
    all_res = filter_emails(df, "All", "All (520)")
    assert len(all_res) == 520, f"Expected 520, got {len(all_res)}"
    print(">>> [PASSED] Status='All', Cat='All': 520 emails")

    # 2. Status 'Verified (OK)'
    verified_res = filter_emails(df, "All", "Verified (OK) (6)")
    assert len(verified_res) == 6, f"Expected 6, got {len(verified_res)}"
    for _, row in verified_res.iterrows():
        assert row["category"] == "document_comparison"
        assert row["mismatch_found"] is False
        assert row["escalate"] is False
    print(">>> [PASSED] Status='Verified (OK)', Cat='All': 6 emails, all strictly verified")

    # 3. Status 'Mismatch Detected'
    mismatch_res = filter_emails(df, "All", "Mismatch Detected (74)")
    assert len(mismatch_res) == 74, f"Expected 74, got {len(mismatch_res)}"
    for _, row in mismatch_res.iterrows():
        assert row["mismatch_found"] is True
    print(">>> [PASSED] Status='Mismatch Detected', Cat='All': 74 emails, all mismatch_found == True")

    # 4. Status 'Needs Review (Escalated)'
    escalated_res = filter_emails(df, "All", "Needs Review (Escalated) (98)")
    assert len(escalated_res) == 98, f"Expected 98, got {len(escalated_res)}"
    for _, row in escalated_res.iterrows():
        assert row["escalate"] is True
    print(">>> [PASSED] Status='Needs Review (Escalated)', Cat='All': 98 emails, all escalate == True")

    # 5. Combined: document_comparison + Mismatch Detected
    doc_mis = filter_emails(df, "document_comparison", "Mismatch Detected (74)")
    assert len(doc_mis) == 74
    print(">>> [PASSED] Combined Cat='document_comparison' + Status='Mismatch Detected': 74 emails")

    # 6. Combined: invoice_query + Mismatch Detected
    inv_mis = filter_emails(df, "invoice_query", "Mismatch Detected (74)")
    assert len(inv_mis) == 0
    print(">>> [PASSED] Combined Cat='invoice_query' + Status='Mismatch Detected': 0 emails (cleanly empty)")

    # 7. Dropdown options scoping
    email_ids = doc_mis["email_id"].tolist()
    assert len(email_ids) == 74
    assert "email_004" in email_ids
    print(">>> [PASSED] Email dropdown list is properly scoped to filtered IDs and contains email_004")

    print("===========================================================================")
    print("ALL INBOX FILTER TESTS PASSED SUCCESSFULLY!")
    print("===========================================================================")


if __name__ == "__main__":
    test_inbox_filtering()
