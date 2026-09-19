"""
classifier.py — Baseline rule-based / heuristic email classifier.

Categorizes shipping operations emails into one of 5 categories:
- 'document_comparison': Requests to verify/compare SI and BL documents
- 'new_si_request': Requests to provide/submit new Shipping Instructions
- 'invoice_query': Queries regarding invoices, billing, charges, freight, THC
- 'general': Operational updates, schedules, delivery plans, general notices
- 'spam': Unsolicited phishing, lottery, scams, or irrelevant promotional emails
"""

from typing import Dict, Any, List


# Keyword lists for deterministic baseline matching
SPAM_KEYWORDS = [
    "weird trick",
    "mailbox has exceeded its storage limit",
    "storage limit",
    "verify your account within",
    "webmail-verify",
    "congratulations!!!",
    "congratulations!",
    "monthly draw",
    "gift card",
    "unpaid customs fee",
    "track-parcel",
    "parcel will be returned",
    "brand new iphone",
    "free-iphone",
    "crypto-invest",
    "claim your",
    "lottery",
    "bitcoin",
]

INVOICE_KEYWORDS = [
    "invoice",
    "invoices",
    "local charge",
    "local charges",
    "telex release charge",
    "telex release charges",
    "billing process",
    "cancel invoice",
    "total freight",
    "thc",
    "d & d charge",
    "d & d charges",
    "demurrage",
    "detention",
    "missing for invoice",
    "billing",
    "payment",
    "credit note",
    "receipt",
]

NEW_SI_KEYWORDS = [
    "request si",
    "requesting si",
    "si needed",
    "need si",
    "cust si",
    "submit si",
    "shipping instruction for",
    "shipping instructions for",
    "please find shipping instruction",
    "revert with draft bl once available",
    "please assist to send the draft bl",
]

COMPARISON_PHRASES = [
    "attached are the si and draft bl",
    "attached are the si and bl",
    "verify the bl matches the si",
    "verify that the bl matches the si",
    "check the details and confirm",
    "to confirm docs",
    "confirm docs",
    "amend bl",
]


def _has_si_and_bl_attachments(attachments: List[str]) -> bool:
    """Check if attachments list contains both SI and BL files."""
    if not attachments:
        return False

    has_si = any(("_si." in a.lower() or "si" in a.lower()) for a in attachments)
    has_bl = any(("_bl." in a.lower() or "bl" in a.lower()) for a in attachments)
    return has_si and has_bl


def classify_email(email: Dict[str, Any]) -> str:
    """
    Classifies a shipping ops email into one of 5 categories using deterministic heuristics.

    Args:
        email: Dictionary containing email fields ('subject', 'body', 'from', 'attachments', etc.)

    Returns:
        One of: 'document_comparison', 'new_si_request', 'invoice_query', 'general', 'spam'
    """
    subject = str(email.get("subject", "")).lower()
    body = str(email.get("body", "")).lower()
    sender = str(email.get("from", "")).lower()
    attachments = email.get("attachments", []) or []

    text_content = f"{subject} {body} {sender}"

    # 1. SPAM check (highest priority filter)
    for kw in SPAM_KEYWORDS:
        if kw in text_content:
            return "spam"

    # 2. INVOICE / BILLING query check
    for kw in INVOICE_KEYWORDS:
        if kw in text_content:
            return "invoice_query"

    # 3. DOCUMENT COMPARISON check
    if _has_si_and_bl_attachments(attachments):
        return "document_comparison"

    for phrase in COMPARISON_PHRASES:
        if phrase in text_content:
            return "document_comparison"

    # 4. NEW SI REQUEST check
    if subject.startswith("si -") or " - si - " in subject or "si needed" in subject:
        return "new_si_request"

    for kw in NEW_SI_KEYWORDS:
        if kw in text_content:
            return "new_si_request"

    # 5. GENERAL messages (fallback)
    return "general"
