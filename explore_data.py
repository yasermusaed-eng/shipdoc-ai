#!/usr/bin/env python3
"""
explore_data.py — Dataset exploration script for the Averis x Monash Hackathon.

Loads raw email records and sample attachments using loader.py's Inbox class,
inspecting field names, JSON structures, category distributions (if any),
and document text format without applying classification logic.
"""

import json
import sys
from collections import Counter
from pathlib import Path

# Resolve paths
PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"

# Add data directory to sys.path to import loader.py
sys.path.insert(0, str(DATA_DIR))

try:
    from loader import Inbox
except ImportError:
    from data.loader import Inbox


def main():
    print("=" * 80)
    print("SHIPPING DOCUMENT VERIFICATION SYSTEM - DATA EXPLORATION")
    print("=" * 80)

    # Initialize Inbox pointing to ./data
    inbox = Inbox(str(DATA_DIR))
    emails = inbox.emails()

    # 1. Total email count
    print(f"\n[1] Total Email Count: {len(emails)}")

    # 2. Check for category breakdown in raw JSON
    categories = []
    category_key_found = None
    possible_keys = ["category", "label", "type", "classification", "intent"]

    for email in emails:
        for k in possible_keys:
            if k in email:
                category_key_found = k
                categories.append(email[k])
                break

    print("\n[2] Email Category Breakdown in Raw JSON:")
    if category_key_found and categories:
        counts = Counter(categories)
        print(f"    Found field '{category_key_found}':")
        for cat, count in counts.most_common():
            print(f"      - {cat}: {count}")
    else:
        print("    No explicit 'category' / 'label' field found in raw email JSON.")
        print("    (Expected: Raw inbox files are unlabelled input records to be classified)")

        # Show all distinct keys across all email JSON objects
        all_keys = set()
        for email in emails:
            all_keys.update(email.keys())
        print(f"    Keys present across raw email objects: {sorted(list(all_keys))}")

    # 3. Full contents of the first 3 emails
    print("\n" + "=" * 80)
    print("[3] Full Contents of First 3 Emails:")
    print("=" * 80)
    for i, email in enumerate(emails[:3], 1):
        print(f"\n--- Email #{i} (email_id: {email.get('email_id', 'N/A')}) ---")
        print(json.dumps(email, indent=2))

    # 4. Find and print raw text of one SI and one BL attachment
    print("\n" + "=" * 80)
    print("[4] Raw Text of Sample SI and BL Attachments (Document Comparison):")
    print("=" * 80)

    selected_email_id = None
    sample_si_path = None
    sample_bl_path = None

    for email in emails:
        attachments = email.get("attachments", [])
        si_matches = [a for a in attachments if "_SI.txt" in a or ("SI" in a and a.endswith(".txt"))]
        bl_matches = [a for a in attachments if "_BL.txt" in a or ("BL" in a and a.endswith(".txt"))]
        if si_matches and bl_matches:
            selected_email_id = email.get("email_id")
            sample_si_path = si_matches[0]
            sample_bl_path = bl_matches[0]
            break

    if sample_si_path and sample_bl_path:
        print(f"\nFound Document-Comparison Email: {selected_email_id}")

        print(f"\n>>> Raw Attachment: {sample_si_path}")
        print("-" * 60)
        si_text = inbox.read_text(sample_si_path)
        print(si_text)
        print("-" * 60)

        print(f"\n>>> Raw Attachment: {sample_bl_path}")
        print("-" * 60)
        bl_text = inbox.read_text(sample_bl_path)
        print(bl_text)
        print("-" * 60)
    else:
        print("No email found with both .txt SI and BL attachments.")


if __name__ == "__main__":
    main()
