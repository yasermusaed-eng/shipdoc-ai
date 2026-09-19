#!/usr/bin/env python3
"""
compare_classifiers.py — Evaluates both heuristic and LLM classifiers side-by-side.

Identifies disagreements between the rule-based baseline and the LLM classifier
to highlight edge cases and assist in verifying classification precision.
"""

import argparse
import sys
from collections import Counter
from pathlib import Path

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
from llm_classifier import classify_email_llm


def main():
    parser = argparse.ArgumentParser(description="Compare heuristic vs LLM email classifiers.")
    parser.add_argument("--limit", type=int, default=None,
                        help="Limit number of emails to evaluate.")
    parser.add_argument("--provider", type=str, default="gemini",
                        choices=["gemini", "openai", "auto"],
                        help="LLM provider to use (default: gemini).")
    args = parser.parse_args()

    print("=" * 80)
    print("CLASSIFIER COMPARISON: HEURISTIC BASELINE vs. LLM")
    print("=" * 80)

    inbox = Inbox(str(DATA_DIR))
    emails = inbox.emails()
    if args.limit:
        emails = emails[:args.limit]

    total = len(emails)
    print(f"Comparing on {total} emails using LLM provider: {args.provider.upper()}\n")

    agreements = 0
    disagreements = []
    disagreement_types = Counter()

    for idx, email in enumerate(emails, 1):
        eid = email.get("email_id", f"email_{idx}")
        subject = email.get("subject", "")
        h_cat = classify_email(email)
        try:
            llm_res = classify_email_llm(email, provider=args.provider)
            l_cat = llm_res["category"]
            l_conf = llm_res["confidence"]
            l_reason = llm_res["reasoning"]
        except Exception as err:
            print(f"[{idx}/{total}] Error calling LLM for {eid}: {err}")
            continue

        if h_cat == l_cat:
            agreements += 1
            print(f"[{idx}/{total}] {eid}: MATCH ({h_cat})")
        else:
            disagreement_types[(h_cat, l_cat)] += 1
            disagreements.append({"id": eid, "subject": subject, "heuristic": h_cat,
                                   "llm": l_cat, "confidence": l_conf, "reasoning": l_reason})
            print(f"[{idx}/{total}] {eid}: DISAGREE -> Heuristic='{h_cat}' | LLM='{l_cat}'")

    print("\n" + "=" * 80)
    print("COMPARISON SUMMARY")
    print("=" * 80)
    disagree_count = len(disagreements)
    agree_pct = (agreements / total * 100) if total else 0
    disagree_pct = (disagree_count / total * 100) if total else 0
    print(f"Total Emails Evaluated : {total}")
    print(f"Agreement Count        : {agreements} ({agree_pct:.1f}%)")
    print(f"Disagreement Count     : {disagree_count} ({disagree_pct:.1f}%)\n")

    if disagreement_types:
        print("Disagreement Breakdown (Heuristic -> LLM):")
        for (h, l), count in disagreement_types.most_common():
            print(f"  - Heuristic '{h}' vs LLM '{l}': {count} occurrences")

    if disagreements:
        print("\n" + "=" * 80)
        print("DETAILED DISAGREEMENT LIST")
        print("=" * 80)
        for d in disagreements:
            print(f"\nEmail ID   : {d['id']}")
            print(f"Subject    : {d['subject']}")
            print(f"Heuristic  : {d['heuristic']}")
            print(f"LLM        : {d['llm']} (confidence: {d['confidence']:.2f})")
            print(f"LLM Reason : {d['reasoning']}")
            print("-" * 60)


if __name__ == "__main__":
    main()
