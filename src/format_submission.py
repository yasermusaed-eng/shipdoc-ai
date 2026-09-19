"""
format_submission.py — Converts pipeline results into official submission format.

Reads output/results.json and reformats it to match sample_submission.json:
- Dict keyed by email_id
- category mapped to uppercase: BL_COMPARISON, SI_REQUEST, INVOICE_QUERY, GENERAL, SPAM
- status mapped to: OK, MISMATCH, NEEDS_REVIEW
- defect_fields: list of field names with mismatches
- has_defect: boolean
- review_reason: normalized to 'missing_attachment' | 'unreadable' | 'wrong_doc_type' | 'missing_value' | null
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_PATH = PROJECT_ROOT / "output" / "results.json"
OUTPUT_PATH = PROJECT_ROOT / "output" / "submission.json"

CATEGORY_MAPPING = {
    "document_comparison": "BL_COMPARISON",
    "new_si_request": "SI_REQUEST",
    "invoice_query": "INVOICE_QUERY",
    "general": "GENERAL",
    "spam": "SPAM",
}

VALID_REVIEW_REASONS = {
    "wrong_doc_type",
    "missing_attachment",
    "unreadable",
    "missing_value",
}


def _normalize_review_reason(reason: Optional[str]) -> Optional[str]:
    """Map internal escalation reasons to the 4 official rubric reasons."""
    if not reason:
        return None
    r_lower = reason.lower()
    if "missing_attachment" in r_lower or "missing si" in r_lower or "missing bl" in r_lower:
        return "missing_attachment"
    if "unreadable" in r_lower or "empty_document" in r_lower or "binary" in r_lower or "decode" in r_lower:
        return "unreadable"
    if "wrong_doc" in r_lower or "wrong_document" in r_lower or "invalid_doc" in r_lower:
        return "wrong_doc_type"
    if "missing_value" in r_lower or "null" in r_lower or "low_confidence" in r_lower:
        return "missing_value"
    return "unreadable"


def convert_results_to_submission(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Converts results list into official submission dictionary."""
    submission: Dict[str, Any] = {}

    for item in results:
        eid = item.get("email_id", "unknown")
        raw_cat = item.get("category", "general")
        category = CATEGORY_MAPPING.get(raw_cat, "GENERAL")

        is_escalated = bool(item.get("escalate", False))
        mismatch_found = item.get("mismatch_found")
        mismatches = item.get("mismatches") or []

        if category == "BL_COMPARISON":
            if is_escalated:
                status = "NEEDS_REVIEW"
                review_reason = _normalize_review_reason(item.get("escalation_reason"))
                has_defect = False
                defect_fields: List[str] = []
            elif mismatch_found is True:
                status = "MISMATCH"
                review_reason = None
                has_defect = True
                defect_fields = sorted(list({m.get("field") for m in mismatches if m.get("field")}))
            else:
                status = "OK"
                review_reason = None
                has_defect = False
                defect_fields = []
        else:
            # Non-comparison emails default to OK in submission schema
            status = "OK"
            review_reason = None
            has_defect = False
            defect_fields = []

        submission[eid] = {
            "category": category,
            "status": status,
            "review_reason": review_reason,
            "defect_fields": defect_fields,
            "has_defect": has_defect,
        }

    return submission


def main():
    print(f"Reading pipeline results from: {INPUT_PATH}")
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        results = json.load(f)

    submission = convert_results_to_submission(results)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(submission, f, indent=2)

    print(f"Successfully generated submission for {len(submission)} emails.")
    print(f"Saved to: {OUTPUT_PATH}")

    # Summary of submission categories and statuses
    from collections import Counter
    cats = Counter(v["category"] for v in submission.values())
    stats = Counter(v["status"] for v in submission.values())
    reasons = Counter(v["review_reason"] for v in submission.values() if v["review_reason"])

    print("\nSubmission Breakdown:")
    print("  Categories:")
    for c, cnt in cats.most_common():
        print(f"    - {c:<18}: {cnt}")
    print("  Statuses:")
    for s, cnt in stats.most_common():
        print(f"    - {s:<18}: {cnt}")
    if reasons:
        print("  Review Reasons:")
        for r, cnt in reasons.most_common():
            print(f"    - {r:<18}: {cnt}")


if __name__ == "__main__":
    main()
