#!/usr/bin/env python3
"""
test_extraction.py — Test script for document field extraction.

Loads a sample SI and BL attachment pair (from email_001 / email_004), runs
extract_fields() on each, and prints the resulting structured JSON.
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


def main():
    print("=" * 80)
    print("TESTING DOCUMENT FIELD EXTRACTION (SI vs. BL)")
    print("=" * 80)

    inbox = Inbox(str(DATA_DIR))

    # Sample attachments from email_001
    si_path = "attachments/email_001_SI.txt"
    bl_path = "attachments/email_001_BL.txt"

    print(f"\n1. Reading SI attachment: {si_path}")
    si_text = inbox.read_text(si_path)
    print("-" * 60)
    print(si_text.strip())
    print("-" * 60)

    print("\n2. Extracting SI fields...")
    si_extracted = extract_fields(si_text)
    print("\n--- Extracted SI JSON ---")
    print(json.dumps(si_extracted, indent=2))

    print("\n" + "=" * 80)
    print(f"3. Reading BL attachment: {bl_path}")
    bl_text = inbox.read_text(bl_path)
    print("-" * 60)
    print(bl_text.strip())
    print("-" * 60)

    print("\n4. Extracting BL fields...")
    bl_extracted = extract_fields(bl_text)
    print("\n--- Extracted BL JSON ---")
    print(json.dumps(bl_extracted, indent=2))

    # Verification assertions
    print("\n" + "=" * 80)
    print("5. Quick Verification Checks:")
    expected_fields = [
        "shipper", "consignee", "notify_party", "port_of_loading",
        "port_of_discharge", "container_count", "gross_weight_kg",
    ]

    si_missing = [f for f in expected_fields if f not in si_extracted]
    bl_missing = [f for f in expected_fields if f not in bl_extracted]

    if not si_missing and not bl_missing:
        print("  [PASSED] All 7 canonical fields present in both SI and BL extraction.")
    else:
        print(f"  [FAILED] Missing fields - SI: {si_missing}, BL: {bl_missing}")

    print("=" * 80)


if __name__ == "__main__":
    main()
