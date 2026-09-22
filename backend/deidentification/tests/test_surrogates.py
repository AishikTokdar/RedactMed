"""Unit tests for synthetic surrogate generation."""

from deidentification.redaction import SurrogateFormatter, redact_text


def test_surrogate_formatter_name_consistency():
    """Verify that repeated mentions of the same name produce identical surrogates."""
    formatter = SurrogateFormatter(seed="clinical-test-seed")

    surrogate1 = formatter.get_tag("person_name", "Rajesh Kumar Sharma")
    surrogate2 = formatter.get_tag("person_name", "Rajesh Kumar Sharma")

    assert surrogate1 == surrogate2
    assert surrogate1 != "Rajesh Kumar Sharma"
    assert not surrogate1.startswith("[")


def test_surrogate_formatter_doctor_prefix():
    """Verify that provider names starting with Dr. retain the professional title."""
    formatter = SurrogateFormatter(seed="clinical-test-seed")
    surrogate = formatter.get_tag("person_name", "Dr. Ananya Deshmukh")

    assert surrogate.startswith("Dr. ")
    assert surrogate != "Dr. Ananya Deshmukh"


def test_surrogate_redaction_pipeline():
    """Verify full text redaction using SurrogateFormatter."""
    text = "Patient Rajesh Kumar Sharma seen by Dr. Ananya Deshmukh at Apollo Hospitals."
    entities = [
        {"type": "person_name", "value": "Rajesh Kumar Sharma"},
        {"type": "person_name", "value": "Dr. Ananya Deshmukh"},
        {"type": "other", "value": "Apollo Hospitals"},
    ]

    formatter = SurrogateFormatter(seed="test-run")
    result = redact_text(text, entities, formatter=formatter)

    # None of the original PHI should appear
    assert "Rajesh Kumar Sharma" not in result.text
    assert "Dr. Ananya Deshmukh" not in result.text
    assert "Apollo Hospitals" not in result.text

    # No generic placeholder tags should appear
    assert "[PERSON_NAME]" not in result.text
    assert "[OTHER]" not in result.text

    # The sentence should read naturally
    assert "seen by" in result.text
    assert "at" in result.text
