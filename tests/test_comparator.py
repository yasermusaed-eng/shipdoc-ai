#!/usr/bin/env python3
"""
test_comparator.py — Test script for deterministic document comparison.

Extracts fields from sample SI/BL documents and validates compare_documents():
1. Perfect match case (email_001) -> reports "No mismatch detected."
2. Defect / mismatch case (email_004) -> detects exact mismatched fields.
"""

import json
import sys
from pathlib import Path

# Setup module resolution
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(DATA_DIR))
sys.path.insert(0, str(SRC_DIR))

try:
    from loader import Inbox
except ImportError:
    from data.loader import Inbox

from extractor import extract_fields
from comparator import compare_documents


def test_matching_pair(inbox: Inbox):
    print("=" * 80)
    print("TEST 1: PERFECT MATCH PAIR (email_001)")
    print("=" * 80)

    si_text = inbox.read_text("attachments/email_001_SI.txt")
    bl_text = inbox.read_text("attachments/email_001_BL.txt")

    si_fields = extract_fields(si_text)
    bl_fields = extract_fields(bl_text)

    result = compare_documents(si_fields, bl_fields)
    print(json.dumps(result, indent=2))

    assert result["mismatch_found"] is False, "Expected mismatch_found to be False"
    assert result["summary"] == "No mismatch detected.", f"Unexpected summary: {result['summary']}"
    print("\n>>> [PASSED] Test 1 reported 'No mismatch detected.'")


def test_mismatch_pair(inbox: Inbox):
    print("\n" + "=" * 80)
    print("TEST 2: MISMATCHED PAIR (email_004)")
    print("=" * 80)

    si_text = inbox.read_text("attachments/email_004_SI.txt")
    bl_text = inbox.read_text("attachments/email_004_BL.txt")

    si_fields = extract_fields(si_text)
    bl_fields = extract_fields(bl_text)

    result = compare_documents(si_fields, bl_fields)
    print(json.dumps(result, indent=2))

    assert result["mismatch_found"] is True, "Expected mismatch_found to be True"
    mismatched_fields = [m["field"] for m in result["mismatches"]]
    print(f"\nDetected mismatched fields: {mismatched_fields}")
    assert "consignee" in mismatched_fields or "notify_party" in mismatched_fields
    print(">>> [PASSED] Test 2 correctly flagged mismatches.")


def main():
    inbox = Inbox(str(DATA_DIR))
    test_matching_pair(inbox)
    test_mismatch_pair(inbox)
    print("\n" + "=" * 80)
    print("ALL COMPARATOR TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    main()
