#!/usr/bin/env python3
"""
run_classification.py — Evaluates the baseline classifier on the entire inbox dataset.

Loops through all emails in ./data/inbox, classifies each email using classify_email(),
and displays a summary table of category counts, percentages, and sample email IDs.
"""

import sys
from collections import Counter, defaultdict
from pathlib import Path

# Setup paths to import from data/ and src/
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(DATA_DIR))
sys.path.insert(0, str(SRC_DIR))

try:
    from loader import Inbox
except ImportError:
    from data.loader import Inbox

from classifier import classify_email


def main():
    print("=" * 70)
    print("RUNNING BASELINE EMAIL CLASSIFICATION (HEURISTIC)")
    print("=" * 70)

    inbox = Inbox(str(DATA_DIR))
    emails = inbox.emails()
    total_emails = len(emails)

    print(f"Loaded {total_emails} emails from: {DATA_DIR / 'inbox'}\n")

    category_counts = Counter()
    category_samples = defaultdict(list)

    for email in emails:
        eid = email.get("email_id", "unknown")
        category = classify_email(email)
        category_counts[category] += 1
        if len(category_samples[category]) < 5:
            category_samples[category].append(eid)

    # Display distribution summary
    print(f"{'Category':<25} {'Count':<10} {'Percentage':<12} {'Sample Email IDs'}")
    print("-" * 75)

    expected_categories = [
        "document_comparison",
        "new_si_request",
        "invoice_query",
        "general",
        "spam",
    ]

    for cat in expected_categories:
        cnt = category_counts[cat]
        pct = (cnt / total_emails * 100) if total_emails > 0 else 0
        samples_str = ", ".join(category_samples[cat])
        print(f"{cat:<25} {cnt:<10} {pct:>6.1f}%     {samples_str}")

    print("-" * 75)
    print(f"{'Total':<25} {total_emails:<10} 100.0%\n")


if __name__ == "__main__":
    main()
