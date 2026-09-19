"""Unit tests for clinical date shifting and perturbation."""

from datetime import datetime
from deidentification.redaction import (
    DateShiftFormatter,
    parse_clinical_date,
    shift_date_string,
    generate_patient_date_shift_days,
    redact_text,
)


def test_parse_clinical_date():
    """Verify recognition of various clinical date formats."""
    # DD/MM/YYYY
    dt, fmt = parse_clinical_date("14/08/1977")
    assert dt is not None
    assert dt.year == 1977 and dt.month == 8 and dt.day == 14

    # YYYY-MM-DD
    dt, fmt = parse_clinical_date("2026-03-12")
    assert dt is not None
    assert dt.year == 2026 and dt.month == 3 and dt.day == 12

    # Ordinal formats like 12th March 2026
    dt, fmt = parse_clinical_date("12th March 2026")
    assert dt is not None
    assert dt.year == 2026 and dt.month == 3 and dt.day == 12


def test_shift_date_string():
    """Verify correct shift calculation and format preservation."""
    # Shift 12/03/2026 by -10 days -> 02/03/2026
    shifted = shift_date_string("12/03/2026", delta_days=-10)
    assert shifted == "02/03/2026"

    # Shift 2026-03-12 by +5 days -> 2026-03-17
    shifted_iso = shift_date_string("2026-03-12", delta_days=5)
    assert shifted_iso == "2026-03-17"


def test_generate_patient_date_shift_days_deterministic():
    """Verify that the generated day shift is deterministic per patient."""
    shift1 = generate_patient_date_shift_days("AH-HYD-2026-88492")
    shift2 = generate_patient_date_shift_days("AH-HYD-2026-88492")
    assert shift1 == shift2
    assert -365 <= shift1 <= -30

    # Different patient gets a different or independent shift
    shift_other = generate_patient_date_shift_days("PATIENT-99999")
    assert -365 <= shift_other <= -30


def test_date_shift_formatter_integration():
    """Verify integration of DateShiftFormatter with redact_text."""
    note = "Patient admitted on 12/03/2026 by Dr. Ananya Deshmukh."
    entities = [
        {"type": "date", "value": "12/03/2026"},
        {"type": "person_name", "value": "Ananya Deshmukh"},
    ]

    formatter = DateShiftFormatter(delta_days=-10)
    result = redact_text(note, entities, formatter=formatter)

    # Date should be shifted to 02/03/2026, Name should be tagged as [PERSON_NAME]
    assert "02/03/2026" in result.text
    assert "[PERSON_NAME]" in result.text
    assert "12/03/2026" not in result.text
