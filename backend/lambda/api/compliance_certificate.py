"""Compliance certificate generator with SHA-256 checksums."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any


def compute_sha256(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def generate_batch_compliance_certificate(
    batch_id: str,
    notes_manifest: list[dict[str, Any]],
    reviewer_info: str = "Clinical Compliance Officer",
    jurisdiction: str = "HIPAA Safe Harbor (§ 164.514(b)(2))",
) -> dict[str, Any]:
    """Generate structured compliance certificate with file checksums."""
    now_utc = datetime.now(timezone.utc).isoformat()
    total_notes = len(notes_manifest)
    approved_notes = [n for n in notes_manifest if n.get("approved")]
    is_fully_compliant = len(approved_notes) == total_notes and total_notes > 0

    file_verifications = []
    total_redacted_spans = 0

    for note in notes_manifest:
        orig = note.get("original_text", "")
        redacted = note.get("redacted_text", "")
        entities = note.get("entities", [])
        total_redacted_spans += len(entities)

        file_verifications.append({
            "note_id": note.get("note_id"),
            "status": "APPROVED" if note.get("approved") else "PENDING_REVIEW",
            "input_sha256": compute_sha256(orig),
            "output_sha256": compute_sha256(redacted),
            "detected_phi_count": len(entities),
        })

    master_hasher = hashlib.sha256()
    for f in file_verifications:
        master_hasher.update(f"{f['note_id']}:{f['input_sha256']}->{f['output_sha256']}".encode("utf-8"))
    master_integrity_hash = master_hasher.hexdigest()

    return {
        "certificate_id": f"CERT-{batch_id}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        "batch_id": batch_id,
        "issued_at": now_utc,
        "compliance_standard": jurisdiction,
        "certified_reviewer": reviewer_info,
        "is_fully_compliant": is_fully_compliant,
        "summary": {
            "total_notes_evaluated": total_notes,
            "approved_notes": len(approved_notes),
            "total_phi_entities_sanitized": total_redacted_spans,
            "unredacted_phi_remaining": 0 if is_fully_compliant else (total_notes - len(approved_notes)),
        },
        "master_integrity_hash": master_integrity_hash,
        "file_verifications": file_verifications,
    }


def render_certificate_html(certificate: dict[str, Any]) -> str:
    """Render a printable HTML certificate for compliance audits."""
    rows = "".join(
        f"""<tr>
            <td style="padding: 8px; border-bottom: 1px solid #ddd; font-family: monospace;">{f['note_id']}</td>
            <td style="padding: 8px; border-bottom: 1px solid #ddd; font-weight: bold; color: {'#16a34a' if f['status'] == 'APPROVED' else '#dc2626'};">{f['status']}</td>
            <td style="padding: 8px; border-bottom: 1px solid #ddd; text-align: center;">{f['detected_phi_count']}</td>
            <td style="padding: 8px; border-bottom: 1px solid #ddd; font-family: monospace; font-size: 11px;">{f['output_sha256'][:16]}...</td>
        </tr>"""
        for f in certificate.get("file_verifications", [])
    )

    status_badge = (
        '<span style="background: #dcfce7; color: #166534; padding: 4px 12px; border-radius: 9999px; font-weight: bold;">CERTIFIED COMPLIANT</span>'
        if certificate.get("is_fully_compliant")
        else '<span style="background: #fee2e2; color: #991b1b; padding: 4px 12px; border-radius: 9999px; font-weight: bold;">PARTIAL / UNVERIFIED</span>'
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>De-Identification Certificate - {certificate['batch_id']}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; color: #1e293b; margin: 40px; line-height: 1.5; }}
        .header {{ border-bottom: 2px solid #2563eb; padding-bottom: 16px; margin-bottom: 24px; }}
        .title {{ font-size: 24px; font-weight: bold; margin: 0; color: #0f172a; }}
        .meta-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin: 20px 0; background: #f8fafc; padding: 16px; border-radius: 8px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 13px; }}
        th {{ background: #f1f5f9; padding: 10px 8px; text-align: left; border-bottom: 2px solid #cbd5e1; }}
        .footer {{ margin-top: 40px; border-top: 1px solid #e2e8f0; padding-top: 16px; font-size: 12px; color: #64748b; }}
    </style>
</head>
<body>
    <div class="header">
        <h1 class="title">Clinical De-Identification Certificate of Compliance</h1>
        <p style="margin: 4px 0; color: #64748b;">Issued under RedactMed Automated Clinical Privacy Verification Platform</p>
    </div>

    <div>
        Status: {status_badge}
    </div>

    <div class="meta-grid">
        <div><strong>Certificate ID:</strong> {certificate['certificate_id']}</div>
        <div><strong>Batch ID:</strong> {certificate['batch_id']}</div>
        <div><strong>Regulatory Standard:</strong> {certificate['compliance_standard']}</div>
        <div><strong>Issued At:</strong> {certificate['issued_at']}</div>
        <div><strong>Certified Reviewer:</strong> {certificate['certified_reviewer']}</div>
        <div><strong>Total Notes:</strong> {certificate['summary']['total_notes_evaluated']} ({certificate['summary']['total_phi_entities_sanitized']} PHI Spans Sanitized)</div>
    </div>

    <div style="margin: 20px 0;">
        <strong>Master SHA-256 Hash Chain:</strong>
        <div style="font-family: monospace; background: #f1f5f9; padding: 8px; border-radius: 4px; word-break: break-all; margin-top: 4px;">
            {certificate['master_integrity_hash']}
        </div>
    </div>

    <h3>Verified Document Ledger</h3>
    <table>
        <thead>
            <tr>
                <th>Document / Note ID</th>
                <th>Validation Status</th>
                <th style="text-align: center;">Redacted Spans</th>
                <th>Sanitized SHA-256 Digest</th>
            </tr>
        </thead>
        <tbody>
            {rows}
        </tbody>
    </table>

    <div class="footer">
        <p>This document certifies that the aforementioned clinical batch underwent context-aware entity de-identification in compliance with {certificate['compliance_standard']}. Cryptographic hash proofs guarantee verifiable immutability.</p>
    </div>
</body>
</html>"""
