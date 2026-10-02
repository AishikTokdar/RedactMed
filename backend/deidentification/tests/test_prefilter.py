"""Unit tests for deterministic regex pre-filter cascade."""

from deidentification import DeterministicRegexFilter, extract_structured_phi


def test_extract_structured_phi_aadhaar():
    """Verify Aadhaar extraction in 4-4-4 format."""
    text = "Patient Aadhaar: 4829-1029-4820 verified at admission."
    results = extract_structured_phi(text)

    types = {r["type"] for r in results}
    values = {r["value"] for r in results}

    assert "aadhaar_number" in types
    assert "4829-1029-4820" in values


def test_extract_structured_phi_ssn_email_ip():
    """Verify standard structured tokens extraction."""
    text = "Contact doc@hospital.org, IP 192.168.1.104, SSN 123-45-6789."
    results = extract_structured_phi(text)

    values = {r["value"] for r in results}
    assert "doc@hospital.org" in values
    assert "192.168.1.104" in values
    assert "123-45-6789" in values


def test_prefilter_merge_with_llm():
    """Verify deduplication when merging LLM and deterministic results."""
    filter_engine = DeterministicRegexFilter()

    llm_entities = [
        {"type": "person_name", "value": "Dr. Smith"},
        {"type": "email", "value": "smith@hospital.org"},
    ]
    det_entities = [
        {"type": "email", "value": "smith@hospital.org"},  # Duplicate
        {"type": "ssn", "value": "999-00-1111"},           # New
    ]

    merged = filter_engine.merge_with_llm(llm_entities, det_entities)
    assert len(merged) == 3

    types = [m["type"] for m in merged]
    assert types.count("email") == 1
    assert "ssn" in types
    assert "person_name" in types
