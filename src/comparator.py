"""
comparator.py — Deterministic comparison engine for shipping document verification.

Performs auditable, rule-based cross-validation between extracted SI (Shipping Instruction)
and BL (Bill of Lading) fields across all 7 canonical logistics dimensions.
No LLM calls are used here to ensure deterministic, auditable decisions.
"""

import re
from typing import Any, Dict, List, Optional

CANONICAL_FIELDS = [
    "shipper", "consignee", "notify_party",
    "port_of_loading", "port_of_discharge",
    "container_count", "gross_weight_kg",
]


def _normalize_string(val: Optional[Any]) -> str:
    """Strip whitespace, collapse spaces/newlines, convert to lowercase."""
    if val is None:
        return ""
    text = str(val).strip().lower()
    text = re.sub(r"[\r\n\t]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    text = text.strip(" ;,.-")
    return text


def _extract_number(val: Optional[Any]) -> Optional[float]:
    """Extract the first numeric value from a string (ignoring thousand-separator commas)."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    cleaned = str(val).replace(",", "").strip()
    match = re.search(r"[-+]?\d*\.?\d+", cleaned)
    if match:
        try:
            return float(match.group())
        except ValueError:
            return None
    return None


def _compare_container_count(si_val: Optional[Any], bl_val: Optional[Any]) -> bool:
    """Compares container counts numerically and by container type spec."""
    si_norm = _normalize_string(si_val)
    bl_norm = _normalize_string(bl_val)
    if si_norm == bl_norm:
        return True
    si_num = _extract_number(si_val)
    bl_num = _extract_number(bl_val)
    if si_num is not None and bl_num is not None:
        if si_num != bl_num:
            return False
        def _get_spec(s: str) -> str:
            s_clean = re.sub(r"\d+", "", s)
            return re.sub(r"[\s'x\-]", "", s_clean)
        si_spec = _get_spec(si_norm)
        bl_spec = _get_spec(bl_norm)
        if si_spec and bl_spec and si_spec != bl_spec:
            return False
        return True
    return si_norm == bl_norm


def _compare_gross_weight(si_val: Optional[Any], bl_val: Optional[Any], tolerance_kg: float = 0.5) -> bool:
    """Compares gross weights numerically with comma-separator and rounding tolerance."""
    si_norm = _normalize_string(si_val)
    bl_norm = _normalize_string(bl_val)
    if si_norm == bl_norm:
        return True
    si_num = _extract_number(si_val)
    bl_num = _extract_number(bl_val)
    if si_num is not None and bl_num is not None:
        return abs(si_num - bl_num) <= tolerance_kg
    return si_norm == bl_norm


def _compare_general_field(si_val: Optional[Any], bl_val: Optional[Any]) -> bool:
    """Compares text fields with case and whitespace normalization."""
    si_norm = _normalize_string(si_val)
    bl_norm = _normalize_string(bl_val)
    if si_norm == bl_norm:
        return True
    if not si_norm or not bl_norm:
        return False
    if si_norm in bl_norm or bl_norm in si_norm:
        shorter, longer = (si_norm, bl_norm) if len(si_norm) < len(bl_norm) else (bl_norm, si_norm)
        if len(shorter) >= 5 and (len(shorter) / len(longer)) >= 0.75:
            return True
    return False


def compare_documents(si_fields: Dict[str, Any], bl_fields: Dict[str, Any]) -> Dict[str, Any]:
    """
    Performs deterministic field-by-field verification of 7 canonical fields between SI and BL.

    Returns:
        {
          "mismatch_found": bool,
          "mismatches": [{"field": ..., "si_value": ..., "bl_value": ...}],
          "summary": str
        }
    """
    mismatches: List[Dict[str, Any]] = []
    for field in CANONICAL_FIELDS:
        si_val = si_fields.get(field)
        bl_val = bl_fields.get(field)
        if field == "container_count":
            match = _compare_container_count(si_val, bl_val)
        elif field == "gross_weight_kg":
            match = _compare_gross_weight(si_val, bl_val)
        else:
            match = _compare_general_field(si_val, bl_val)
        if not match:
            mismatches.append({"field": field, "si_value": si_val, "bl_value": bl_val})

    mismatch_found = len(mismatches) > 0
    if not mismatch_found:
        summary = "No mismatch detected."
    else:
        diff_descriptions = [
            f"{m['field']} (SI: '{m['si_value']}' vs BL: '{m['bl_value']}')"
            for m in mismatches
        ]
        summary = f"Mismatches detected in {len(mismatches)} field(s): " + "; ".join(diff_descriptions)

    return {"mismatch_found": mismatch_found, "mismatches": mismatches, "summary": summary}
