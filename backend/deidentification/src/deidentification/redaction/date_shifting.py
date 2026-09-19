"""Longitudinal date shifting preserving clinical intervals per patient."""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timedelta
from typing import Any

DATE_PATTERNS: list[tuple[re.Pattern[str], str, str]] = [
    (re.compile(r"^(\d{4})-(\d{1,2})-(\d{1,2})$"), "%Y-%m-%d", "%Y-%m-%d"),
    (re.compile(r"^(\d{1,2})/(\d{1,2})/(\d{4})$"), "%d/%m/%Y", "%d/%m/%Y"),
    (re.compile(r"^(\d{1,2})-(\d{1,2})-(\d{4})$"), "%d-%m-%Y", "%d-%m-%Y"),
    (re.compile(r"^(\d{1,2})/(\d{1,2})/(\d{4})$"), "%m/%d/%Y", "%m/%d/%Y"),
    (re.compile(r"^(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+(\d{1,2}),?\s+(\d{4})$", re.IGNORECASE), "%B %d, %Y", "%B %d, %Y"),
    (re.compile(r"^(\d{1,2})(?:st|nd|rd|th)?\s+(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+(\d{4})$", re.IGNORECASE), "%d %B %Y", "%d %B %Y"),
]


def parse_clinical_date(date_str: str) -> tuple[datetime | None, str | None]:
    """Parse clinical date across common healthcare formats."""
    clean_str = date_str.strip()
    normalized = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", clean_str, flags=re.IGNORECASE)

    for pattern, parse_fmt, out_fmt in DATE_PATTERNS:
        match = pattern.match(clean_str) or pattern.match(normalized)
        if match:
            for fmt in (parse_fmt, "%b %d, %Y", "%d %b %Y"):
                try:
                    return datetime.strptime(normalized, fmt), out_fmt
                except ValueError:
                    continue

    return None, None


def shift_date_string(date_str: str, delta_days: int) -> str:
    """Shift date string by delta days while preserving format."""
    dt, out_fmt = parse_clinical_date(date_str)
    if dt is None or out_fmt is None:
        return "[DATE_SHIFTED]"

    shifted_dt = dt + timedelta(days=delta_days)
    return shifted_dt.strftime(out_fmt)


def generate_patient_date_shift_days(
    patient_identifier: str,
    salt: str = "redactmed-date-salt",
    min_days: int = -365,
    max_days: int = -30,
) -> int:
    """Derive deterministic day offset for a patient."""
    digest = hashlib.sha256(f"{salt}:{patient_identifier}".encode("utf-8")).hexdigest()
    int_seed = int(digest[:8], 16)
    span = abs(max_days - min_days) + 1
    return min_days + (int_seed % span)


class DateShiftFormatter:
    """Formatter that shifts dates while preserving tags for other PHI."""

    def __init__(
        self,
        delta_days: int = -42,
        base_formatter: Any = None,
    ) -> None:
        self.delta_days = delta_days
        self.base_formatter = base_formatter

    def get_tag(self, pii_type: str, value: str) -> str:
        if pii_type.lower() == "date":
            return shift_date_string(value, self.delta_days)

        if self.base_formatter is not None:
            return self.base_formatter.get_tag(pii_type, value)

        return f"[{pii_type.upper()}]"

    def reset(self) -> None:
        if self.base_formatter and hasattr(self.base_formatter, "reset"):
            self.base_formatter.reset()
