"""Deterministic regex pre-filter for clinical PII identification."""

from __future__ import annotations

import re
from typing import Any

AADHAAR_REGEX = re.compile(r"\b[2-9]\d{3}[\s-]\d{4}[\s-]\d{4}\b")
PAN_REGEX = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b")
ABHA_REGEX = re.compile(r"\b\d{2}-\d{4}-\d{4}-\d{4}\b")
EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
URL_REGEX = re.compile(r"https?://(?:www\.)?[-a-zA-Z0-9@:%._+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_+.~#?&/=]*)")
IP_REGEX = re.compile(r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b")
US_SSN_REGEX = re.compile(r"\b(?!000|666|9\d{2})\d{3}[-\s](?!00)\d{2}[-\s](?!0000)\d{4}\b")
MRN_REGEX = re.compile(r"\b(?:MRN|MEDREC|EMR|PATIENT ID|CHART NO)[\s:#]*([A-Z0-9]{5,12})\b", re.IGNORECASE)


class DeterministicRegexFilter:
    """Fast regular expression extractor for standard clinical PII identifiers."""

    def __init__(self, jurisdiction: str = "HIPAA") -> None:
        self.jurisdiction = jurisdiction.upper()

    def extract_phi_spans(self, text: str) -> list[dict[str, Any]]:
        spans: list[dict[str, Any]] = []

        for match in US_SSN_REGEX.finditer(text):
            spans.append({"type": "ssn", "value": match.group(0), "confidence": 1.0, "source": "regex"})

        for match in EMAIL_REGEX.finditer(text):
            spans.append({"type": "email", "value": match.group(0), "confidence": 1.0, "source": "regex"})

        for match in IP_REGEX.finditer(text):
            spans.append({"type": "ip_address", "value": match.group(0), "confidence": 1.0, "source": "regex"})

        for match in URL_REGEX.finditer(text):
            spans.append({"type": "url", "value": match.group(0), "confidence": 1.0, "source": "regex"})

        for match in MRN_REGEX.finditer(text):
            mrn_val = match.group(1) if match.lastindex else match.group(0)
            spans.append({"type": "medical_record_number", "value": mrn_val, "confidence": 0.95, "source": "regex"})

        if self.jurisdiction == "DPDP_INDIA":
            for match in AADHAAR_REGEX.finditer(text):
                spans.append({"type": "aadhaar_number", "value": match.group(0), "confidence": 1.0, "source": "regex"})
            for match in PAN_REGEX.finditer(text):
                spans.append({"type": "pan_number", "value": match.group(0), "confidence": 1.0, "source": "regex"})
            for match in ABHA_REGEX.finditer(text):
                spans.append({"type": "abha_id", "value": match.group(0), "confidence": 1.0, "source": "regex"})

        return spans


def merge_extracted_entities(
    regex_entities: list[dict[str, Any]],
    llm_entities: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Merge and deduplicate entities from deterministic regex and LLM passes."""
    merged: list[dict[str, Any]] = list(regex_entities)
    seen_values = {e["value"].strip().lower() for e in regex_entities}

    for ent in llm_entities:
        val_clean = ent["value"].strip().lower()
        if val_clean not in seen_values and len(val_clean) > 0:
            merged.append(ent)
            seen_values.add(val_clean)

    return merged
