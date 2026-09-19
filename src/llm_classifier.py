"""
llm_classifier.py — LLM-based email classification for shipping operations.

Uses Google Gemini (with automatic OpenAI fallback if configured) to classify
inbox emails into 5 target categories with confidence scores and reasoning.
"""

import json
import os
import re
from typing import Any, Dict
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

SYSTEM_PROMPT = """You are an expert shipping operations AI assistant. Your task is to accurately classify incoming logistics emails into exactly ONE of the following 5 categories:

1. document_comparison: Requests to verify, confirm, or cross-check details between a Shipping Instruction (SI) and draft Bill of Lading (BL).
2. new_si_request: Requests to create, issue, or submit new Shipping Instructions (SI) containing booking or cargo details.
3. invoice_query: Queries or updates regarding invoices, local charges, THC, freight billing, detention/demurrage, or payment status.
4. general: Operational status updates, vessel schedules, delivery summaries, or administrative notifications.
5. spam: Phishing attempts, prize/lottery promotions, mailbox quota alerts, delivery fee scams, or irrelevant unsolicited messages.

Return ONLY a valid JSON object with this exact structure:
{
  "category": "document_comparison" | "new_si_request" | "invoice_query" | "general" | "spam",
  "confidence": <float between 0.0 and 1.0>,
  "reasoning": "<concise 1-2 sentence explanation of why this category was selected>"
}
"""

VALID_CATEGORIES = {
    "document_comparison",
    "new_si_request",
    "invoice_query",
    "general",
    "spam",
}


def _call_gemini(email_content: str, model_name: str = "gemini-2.5-flash") -> Dict[str, Any]:
    """Call Google Gemini API using google-genai SDK or direct REST request."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set.")

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        prompt = f"{SYSTEM_PROMPT}\n\nEmail to classify:\n{email_content}"
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.1,
            ),
        )
        return json.loads(response.text)
    except ImportError:
        import requests
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": f"{SYSTEM_PROMPT}\n\nEmail to classify:\n{email_content}"}]}],
            "generationConfig": {"responseMimeType": "application/json", "temperature": 0.1},
        }
        res = requests.post(url, json=payload, timeout=30)
        res.raise_for_status()
        data = res.json()
        raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(raw_text)


def _call_openai(email_content: str, model_name: str = "gpt-4o-mini") -> Dict[str, Any]:
    """Fallback call to OpenAI API."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("Neither GEMINI_API_KEY nor OPENAI_API_KEY is set.")

    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Email to classify:\n{email_content}"},
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
    )
    raw_text = response.choices[0].message.content
    return json.loads(raw_text)


def classify_email_llm(email: Dict[str, Any], provider: str = "gemini") -> Dict[str, Any]:
    """
    Classify an email using an LLM (Gemini by default, with OpenAI fallback).

    Args:
        email: Dictionary representing email record.
        provider: 'gemini' or 'openai'

    Returns:
        Dict: {"category": str, "confidence": float, "reasoning": str}
    """
    email_id = email.get("email_id", "N/A")
    subject = email.get("subject", "")
    sender = email.get("from", "")
    body = email.get("body", "")
    attachments = email.get("attachments", [])

    email_content = (
        f"Email ID: {email_id}\n"
        f"From: {sender}\n"
        f"Subject: {subject}\n"
        f"Attachments: {json.dumps(attachments)}\n"
        f"Body:\n{body}\n"
    )

    result = None
    if provider == "gemini" or (provider == "auto" and os.getenv("GEMINI_API_KEY")):
        try:
            result = _call_gemini(email_content)
        except Exception as e:
            if os.getenv("OPENAI_API_KEY"):
                result = _call_openai(email_content)
            else:
                raise e
    else:
        result = _call_openai(email_content)

    cat = str(result.get("category", "general")).strip().lower().replace("-", "_").replace(" ", "_")
    if cat not in VALID_CATEGORIES:
        if "compare" in cat or "comparison" in cat or "bl" in cat:
            cat = "document_comparison"
        elif "si" in cat and "request" in cat:
            cat = "new_si_request"
        elif "invoice" in cat or "bill" in cat or "charge" in cat:
            cat = "invoice_query"
        elif "spam" in cat or "phish" in cat:
            cat = "spam"
        else:
            cat = "general"

    confidence = float(result.get("confidence", 0.9))
    reasoning = str(result.get("reasoning", "Classified based on email content analysis."))

    return {"category": cat, "confidence": confidence, "reasoning": reasoning}
