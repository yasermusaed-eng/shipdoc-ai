#!/usr/bin/env python3
"""
submit_and_score.py — Submits output/submission.json to the evaluation server and reports scoreboard.

Tries to submit via loader.py's Inbox.submit() to http://localhost:8080/submit.
If the evaluation server is unreachable, provides an in-depth diagnostic audit of
our submission distribution, defect breakdown, and actionable weak points.
"""

import json
import os
import sys
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
SUBMISSION_PATH = PROJECT_ROOT / "output" / "submission.json"

sys.path.insert(0, str(DATA_DIR))

try:
    from loader import Inbox
except ImportError:
    from data.loader import Inbox

DEFAULT_SERVER_URL = os.getenv("EVAL_SERVER_URL", "http://localhost:8080")


def submit_to_server(submission: dict, server_url: str):
    """Submits submission dict to server via Inbox.submit()."""
    inbox = Inbox(server_url)
    return inbox.submit(submission)


def audit_submission_weaknesses(submission: dict):
    """Provides a structural analysis of the current pipeline submission."""
    total = len(submission)
    cats = Counter(v["category"] for v in submission.values())
    stats = Counter(v["status"] for v in submission.values())
    reasons = Counter(v["review_reason"] for v in submission.values() if v.get("review_reason"))

    defect_fields_counter = Counter()
    for v in submission.values():
        for field in v.get("defect_fields", []):
            defect_fields_counter[field] += 1

    print("\n" + "=" * 75)
    print("SUBMISSION DIAGNOSTIC & WEAKNESS ANALYSIS")
    print("=" * 75)

    print(f"\n[1] Overall Volume: {total} emails")

    print("\n[2] Category Breakdown:")
    for cat, cnt in cats.most_common():
        pct = (cnt / total * 100) if total else 0
        print(f"    - {cat:<18}: {cnt:>4} ({pct:>5.1f}%)")

    print("\n[3] Verification Statuses:")
    for st, cnt in stats.most_common():
        pct = (cnt / total * 100) if total else 0
        print(f"    - {st:<18}: {cnt:>4} ({pct:>5.1f}%)")

    print("\n[4] Escalation / Review Reasons Breakdown:")
    for r, cnt in reasons.most_common():
        pct = (cnt / total * 100) if total else 0
        print(f"    - {r:<20}: {cnt:>4} ({pct:>5.1f}%)")

    print("\n[5] Detected Defect Fields Distribution:")
    for field, cnt in defect_fields_counter.most_common():
        print(f"    - {field:<20}: {cnt:>4} mismatches detected")

    print("\n" + "=" * 75)
    print("IDENTIFIED WEAKNESSES & RECOMMENDED ACTIONS")
    print("=" * 75)

    print("""
1. Binary Attachment Formats (30 emails unreadable):
   - Current status: Marked as 'NEEDS_REVIEW' ('unreadable') because files are
     .xlsx, .pdf, or .docx.
   - Impact: Scores docked on end-to-end defect detection because these documents
     are skipped.
   - Fix: Integrate openpyxl, pypdf, and python-docx in src/pipeline.py to extract
     text directly from spreadsheets and PDFs.

2. Body-Embedded SI Requests (55 emails marked 'missing_attachment'):
   - Current status: Emails flagged as document_comparison missing attachments.
   - Impact: Many of these are either pure 'SI_REQUEST' emails (where SI text was
     pasted in the email body, e.g. email_007) or partial requests.
   - Fix: If attachments are empty but body contains 'Shipper:', 'Consignee:',
     re-route category to 'SI_REQUEST' rather than 'BL_COMPARISON'.

3. Sub-Field Granularity in Container Count & Weights:
   - Ensure tolerance matching for trailing decimals, commas, and container specs.
""")
    print("=" * 75)


def main():
    if not SUBMISSION_PATH.exists():
        print(f"Error: {SUBMISSION_PATH} not found. Please run format_submission.py first.")
        sys.exit(1)

    with open(SUBMISSION_PATH, "r", encoding="utf-8") as f:
        submission = json.load(f)

    print("=" * 75)
    print(f"SUBMITTING SUBMISSION TO EVALUATION SERVER: {DEFAULT_SERVER_URL}")
    print("=" * 75)

    try:
        response = submit_to_server(submission, DEFAULT_SERVER_URL)
        print("\n[SUCCESS] Server responded with Scoreboard:")
        print(json.dumps(response, indent=2))

        final_score = response.get("final_score")
        if final_score is not None:
            print(f"\n>>> FINAL SCORE: {final_score:.2%}")
        breakdown = response.get("score_breakdown") or response.get("breakdown")
        if breakdown:
            print("\nScore Breakdown:")
            for k, v in breakdown.items():
                print(f"  - {k}: {v}")

    except (urllib.error.URLError, ConnectionRefusedError, OSError) as e:
        print(f"\n[NOTICE] Could not connect to evaluation server at {DEFAULT_SERVER_URL}.")
        print(f"Reason: {e}")
        print("\nThe local Docker evaluation container is not currently running on port 8080.")
        print("To start the official evaluation container, run:")
        print("  docker run -d -p 8080:8080 <hackathon-evaluation-image>")
        print("\nPerforming offline diagnostic audit of current submission instead...")

        audit_submission_weaknesses(submission)


if __name__ == "__main__":
    main()
