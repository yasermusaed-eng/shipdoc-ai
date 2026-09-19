#!/usr/bin/env python3
"""
test_verification_metrics.py — Unit test validating the scoped "Verified OK" calculation
and the mathematical invariant: mismatches + escalations + verified_ok == total comparisons.
"""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
SRC_DIR = PROJECT_ROOT / "src"
OUTPUT_DIR = PROJECT_ROOT / "output"

sys.path.insert(0, str(DATA_DIR))
sys.path.insert(0, str(SRC_DIR))

from ui_common import compute_verification_metrics


def test_metrics_on_actual_dataset():
    print("=" * 75)
    print("TEST: Scoped Verification Metrics on Actual Dataset")
    print("=" * 75)

    results_path = OUTPUT_DIR / "results.json"
    assert results_path.exists(), f"results.json must exist at {results_path}"
    
    with open(results_path, "r", encoding="utf-8") as f:
        results = json.load(f)

    metrics = compute_verification_metrics(results)
    
    print(f"Total Emails Processed : {metrics['total_emails']}")
    print(f"Total SI/BL Checks     : {metrics['comparisons']}")
    print(f"Mismatches Flagged     : {metrics['mismatches']}")
    print(f"Escalations Flagged    : {metrics['escalations']}")
    print(f"Verified OK (Scoped)   : {metrics['verified_ok']}")

    # Expected numbers
    assert metrics["total_emails"] == 520, f"Expected 520 total emails, got {metrics['total_emails']}"
    assert metrics["comparisons"] == 178, f"Expected 178 comparisons, got {metrics['comparisons']}"
    assert metrics["mismatches"] == 74, f"Expected 74 mismatches, got {metrics['mismatches']}"
    assert metrics["escalations"] == 98, f"Expected 98 escalations, got {metrics['escalations']}"
    assert metrics["verified_ok"] == 6, f"Expected 6 verified OK, got {metrics['verified_ok']} (must NOT be 348)"

    # Invariant assertion
    assert (
        metrics["mismatches"] + metrics["escalations"] + metrics["verified_ok"] == metrics["comparisons"]
    ), "Invariant failed: mismatches + escalations + verified_ok must strictly equal total comparisons!"

    print(">>> [PASSED] Invariant verified: 74 + 98 + 6 == 178.")

    # Non-comparison emails must have mismatch_found is None AND escalate is None
    non_comp = [r for r in results if r.get("category") != "document_comparison"]
    assert len(non_comp) == 342, f"Expected 342 non-comparison emails, got {len(non_comp)}"
    for r in non_comp:
        assert r.get("mismatch_found") is None, f"{r['email_id']} mismatch_found must be None, got {r.get('mismatch_found')}"
        assert r.get("escalate") is None, f"{r['email_id']} escalate must be None, got {r.get('escalate')}"
    print(">>> [PASSED] Verified all 342 non-comparison emails strictly have null mismatch_found and escalate.")


def test_assertion_triggers_on_bad_data():
    print("\n" + "=" * 75)
    print("TEST: Sanity Check Invariant Triggers On Inconsistent Data")
    print("=" * 75)

    # Synthetic bad data where one document_comparison record is missing outcome
    bad_data = [
        {"category": "document_comparison", "mismatch_found": True, "escalate": False},
        {"category": "document_comparison", "mismatch_found": None, "escalate": False}, # Broken outcome
    ]

    try:
        compute_verification_metrics(bad_data)
        assert False, "Should have raised AssertionError due to broken invariant"
    except AssertionError as e:
        print(f">>> [PASSED] Successfully caught invariant violation: {e}")


if __name__ == "__main__":
    test_metrics_on_actual_dataset()
    test_assertion_triggers_on_bad_data()
    print("\n" + "=" * 75)
    print("ALL VERIFICATION METRIC TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 75)
