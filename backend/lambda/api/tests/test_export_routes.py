"""Unit tests for batch export API routes."""

import base64
import json
import zipfile
import io
from unittest.mock import patch

from route_handlers import export_batch


def test_export_batch_not_found():
    """Verify 404 returned when batch has no files."""
    with patch("storage.list_keys", return_value=[]):
        code, resp = export_batch({"batch_id": "non-existent"}, {}, {})
        assert code == 404
        assert "error" in resp


def test_export_batch_json():
    """Verify JSON structured export format."""
    mock_keys = ["batch-001/input/note1.txt", "batch-001/input/note2.txt"]

    with patch("storage.list_keys", return_value=mock_keys), \
         patch("storage.stem", side_effect=lambda k: k.split("/")[-1].replace(".txt", "")), \
         patch("route_handlers.get_saved_redacted_text", return_value="Approved redacted text"), \
         patch("storage.read_text", return_value="Output redacted text"), \
         patch("storage.read_json", return_value={"pii_entities": [{"type": "NAME", "value": "John"}]}):

        code, resp = export_batch({"batch_id": "batch-001"}, {}, {"format": "json"})
        assert code == 200
        assert resp["batch_id"] == "batch-001"
        assert resp["format"] == "json"
        assert resp["total_notes"] == 2
        assert resp["approved_notes"] == 2
        assert len(resp["notes"]) == 2
        assert resp["notes"][0]["note_id"] == "note1"


def test_export_batch_csv():
    """Verify CSV audit report format."""
    mock_keys = ["batch-001/input/note1.txt"]

    with patch("storage.list_keys", return_value=mock_keys), \
         patch("storage.stem", return_value="note1"), \
         patch("route_handlers.get_saved_redacted_text", return_value="Approved text"), \
         patch("storage.read_text", return_value="Output text"), \
         patch("storage.read_json", return_value={"pii_entities": [{"type": "NAME", "value": "John"}]}):

        code, resp = export_batch({"batch_id": "batch-001"}, {}, {"format": "csv"})
        assert code == 200
        assert resp["format"] == "csv"
        assert "note_id,approved,entity_count" in resp["content"]
        assert '"note1",True,1,"NAME"' in resp["content"]


def test_export_batch_zip():
    """Verify ZIP archive creation and extraction."""
    mock_keys = ["batch-001/input/note1.txt"]

    with patch("storage.list_keys", return_value=mock_keys), \
         patch("storage.stem", return_value="note1"), \
         patch("route_handlers.get_saved_redacted_text", return_value="Sanitized content"), \
         patch("storage.read_text", return_value="Output text"), \
         patch("storage.read_json", return_value={}):

        code, resp = export_batch({"batch_id": "batch-001"}, {}, {"format": "zip"})
        assert code == 200
        assert resp["format"] == "zip"
        assert resp["filename"] == "batch-001_redacted.zip"

        # Verify ZIP unzips cleanly
        zip_bytes = base64.b64decode(resp["data_base64"])
        with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
            namelist = zf.namelist()
            assert "note1_redacted.txt" in namelist
            extracted = zf.read("note1_redacted.txt").decode("utf-8")
            assert extracted == "Sanitized content"
