"""Unit tests for compliance certificate generation."""

from compliance_certificate import (
    compute_sha256,
    generate_batch_compliance_certificate,
    render_certificate_html,
)


def test_compute_sha256():
    """Verify SHA-256 calculation."""
    digest = compute_sha256("test clinical string")
    assert isinstance(digest, str)
    assert len(digest) == 64


def test_generate_compliance_certificate_fully_compliant():
    """Verify certificate generation for 100% approved batch."""
    manifest = [
        {
            "note_id": "note-001",
            "original_text": "Patient John Smith",
            "redacted_text": "Patient [NAME]",
            "approved": True,
            "entities": [{"type": "NAME", "value": "John Smith"}],
        },
        {
            "note_id": "note-002",
            "original_text": "Patient Jane Doe",
            "redacted_text": "Patient [NAME]",
            "approved": True,
            "entities": [{"type": "NAME", "value": "Jane Doe"}],
        },
    ]

    cert = generate_batch_compliance_certificate("batch-test", manifest)
    assert cert["is_fully_compliant"] is True
    assert cert["summary"]["total_notes_evaluated"] == 2
    assert cert["summary"]["approved_notes"] == 2
    assert cert["summary"]["total_phi_entities_sanitized"] == 2
    assert cert["summary"]["unredacted_phi_remaining"] == 0
    assert cert["master_integrity_hash"] is not None
    assert len(cert["file_verifications"]) == 2


def test_render_certificate_html():
    """Verify HTML rendering containing required compliance headings and badges."""
    manifest = [
        {
            "note_id": "note-001",
            "original_text": "Raw note",
            "redacted_text": "Sanitized note",
            "approved": True,
            "entities": [{"type": "NAME", "value": "John"}],
        }
    ]
    cert = generate_batch_compliance_certificate("batch-test", manifest)
    html = render_certificate_html(cert)

    assert "<!DOCTYPE html>" in html
    assert "Clinical De-Identification Certificate of Compliance" in html
    assert "CERTIFIED COMPLIANT" in html
    assert cert["master_integrity_hash"] in html
    assert "note-001" in html
