"""
extractor.py — LLM-driven structured field extraction for shipping documents (SI & BL).

Extracts 7 canonical shipment fields from unstructured document text:
- shipper, consignee, notify_party, port_of_loading, port_of_discharge,
  container_count, gross_weight_kg
"""

import json
import os
import re
from typing import Any, Dict, Optional
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

EXTRACTION_SYSTEM_PROMPT = """You are an expert shipping document parser.
Extract the 7 canonical logistics fields from the provided Shipping Instruction (SI) or Bill of Lading (BL) document text.

Align varied industry terminology to these exact canonical keys:
1. "shipper": Shipper, Exporter, Shipper/Exporter, From
2. "consignee": Consignee, Consignee (Non-Negotiable), To the Order of, Receiver
3. "notify_party": Notify Party, Notify, Also Notify
4. "port_of_loading": Port of Loading, POL, Load Port, Port of Departure
5. "port_of_discharge": Port of Discharge, POD, Discharge Port, Destination Port
6. "container_count": Container Count, Total Containers, No. of Containers or Packages
7. "gross_weight_kg": Gross Weight (KG), Gross Wt (kgs), Total Gross Weight

RULES:
- Return ONLY a valid JSON object with all 7 keys.
- If a field is missing, not stated, or unreadable in the text, set its value to null.
- DO NOT invent, hallucinate, or guess values.
- Retain complete company names and addresses where present under shipper/consignee.

Output Format:
{
  "shipper": string or null,
  "consignee": string or null,
  "notify_party": string or null,
  "port_of_loading": string or null,
  "port_of_discharge": string or null,
  "container_count": string or null,
  "gross_weight_kg": string or null
}
"""

CANONICAL_FIELDS = [
    "shipper", "consignee", "notify_party",
    "port_of_loading", "port_of_discharge",
    "container_count", "gross_weight_kg",
]


def _call_gemini_extraction(doc_text: str, model_name: str = "gemini-2.5-flash") -> Dict[str, Any]:
    """Call Google Gemini with structured JSON output."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set.")
    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=api_key)
        prompt = f"{EXTRACTION_SYSTEM_PROMPT}\n\nDocument Text:\n{doc_text}"
        response = client.models.generate_content(
            model=model_name, contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.0),
        )
        return json.loads(response.text)
    except ImportError:
        import requests
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": f"{EXTRACTION_SYSTEM_PROMPT}\n\nDocument Text:\n{doc_text}"}]}],
            "generationConfig": {"responseMimeType": "application/json", "temperature": 0.0},
        }
        res = requests.post(url, json=payload, timeout=30)
        res.raise_for_status()
        return json.loads(res.json()["candidates"][0]["content"]["parts"][0]["text"])


def _call_openai_extraction(doc_text: str, model_name: str = "gpt-4o-mini") -> Dict[str, Any]:
    """Call OpenAI with structured JSON output."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set.")
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
            {"role": "user", "content": f"Document Text:\n{doc_text}"},
        ],
        response_format={"type": "json_object"}, temperature=0.0,
    )
    return json.loads(response.choices[0].message.content)


def _heuristic_fallback_extractor(doc_text: str) -> Dict[str, Optional[str]]:
    """Deterministic regex fallback for offline testing without API keys."""
    result: Dict[str, Optional[str]] = {f: None for f in CANONICAL_FIELDS}
    lines = doc_text.splitlines()
    patterns = {
        "shipper": [r"^(?:shipper/exporter|shipper)\s*:\s*(.+)$"],
        "consignee": [r"^(?:consignee\s*(?:\([^)]+\))?|to the order of)\s*:\s*(.+)$"],
        "notify_party": [r"^(?:notify party|notify)\s*:\s*(.+)$"],
        "port_of_loading": [r"^(?:port of loading\s*(?:\([^)]+\))?|load port|pol)\s*:\s*(.+)$"],
        "port_of_discharge": [r"^(?:discharge port|port of discharge\s*(?:\([^)]+\))?|pod)\s*:\s*(.+)$"],
        "container_count": [r"^(?:no\. of containers or packages|container count|total containers)\s*:\s*(.+)$"],
        "gross_weight_kg": [r"^(?:gross weight\s*(?:\([^)]+\))?|gross wt\s*(?:\([^)]+\))?)\s*:\s*(.+)$"],
    }
    for i, line in enumerate(lines):
        line_clean = line.strip()
        for field, reg_list in patterns.items():
            if result[field] is not None:
                continue
            for pattern in reg_list:
                m = re.match(pattern, line_clean, re.IGNORECASE)
                if m:
                    val = m.group(1).strip()
                    if field in ("shipper", "consignee") and i + 1 < len(lines):
                        next_line = lines[i + 1]
                        if next_line.startswith("  ") and next_line.strip():
                            val = f"{val}\n  {next_line.strip()}"
                    result[field] = val
                    break
    return result


def extract_fields(document_text: str, provider: str = "auto") -> Dict[str, Optional[str]]:
    """
    Extracts the 7 canonical shipping fields from document text.
    Falls back to heuristic regex extractor if no API keys are configured.
    """
    if not document_text or not document_text.strip():
        return {f: None for f in CANONICAL_FIELDS}

    has_gemini = bool(os.getenv("GEMINI_API_KEY"))
    has_openai = bool(os.getenv("OPENAI_API_KEY"))
    parsed = None

    if (provider in ("gemini", "auto") and has_gemini) or (provider == "gemini"):
        try:
            parsed = _call_gemini_extraction(document_text)
        except Exception:
            if has_openai and provider == "auto":
                parsed = _call_openai_extraction(document_text)
            else:
                parsed = _heuristic_fallback_extractor(document_text)
    elif (provider in ("openai", "auto") and has_openai) or (provider == "openai"):
        try:
            parsed = _call_openai_extraction(document_text)
        except Exception:
            parsed = _heuristic_fallback_extractor(document_text)
    else:
        parsed = _heuristic_fallback_extractor(document_text)

    normalized: Dict[str, Optional[str]] = {}
    for f in CANONICAL_FIELDS:
        val = parsed.get(f)
        if val is None or str(val).strip().lower() in ("null", "none", "", "n/a"):
            normalized[f] = None
        else:
            normalized[f] = str(val).strip()
    return normalized
