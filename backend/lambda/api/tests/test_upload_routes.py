import os
import unittest
from unittest.mock import patch

os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
os.environ.setdefault("BUCKET_NAME", "test-bucket")
os.environ.setdefault("STATS_TABLE_NAME", "test-stats")
os.environ.setdefault("QUEUE_URL", "https://sqs.us-east-1.amazonaws.com/123/queue")
os.environ.setdefault("DLQ_URL", "https://sqs.us-east-1.amazonaws.com/123/dlq")
os.environ.setdefault("INGESTION_FUNCTION_NAME", "test-ingestion")

import route_handlers as handlers
import storage


class TestUploadRouteHandlers(unittest.TestCase):
    """Test cases for request_upload_urls and upload_batch_files handlers."""

    @patch("route_handlers.initialize_batch_stats")
    @patch("storage.generate_presigned_upload_url")
    def test_request_upload_urls_success(self, mock_presign, mock_init_stats):
        mock_presign.return_value = "https://s3.amazonaws.com/test-bucket/presigned-url"

        body = {
            "batch_id": "test-batch-001",
            "files": [
                {"filename": "note1.txt", "content_type": "text/plain"},
                {"filename": "subfolder/note2.txt", "content_type": "text/plain"},
            ],
        }

        status, resp = handlers.request_upload_urls({}, body, {})
        self.assertEqual(status, 200)
        self.assertEqual(resp["batch_id"], "test-batch-001")
        self.assertEqual(len(resp["urls"]), 2)
        self.assertEqual(resp["urls"][0]["filename"], "note1.txt")
        self.assertEqual(resp["urls"][1]["filename"], "note2.txt")
        self.assertEqual(resp["urls"][0]["upload_url"], "https://s3.amazonaws.com/test-bucket/presigned-url")
        mock_init_stats.assert_called_once_with("test-batch-001", 2)

    def test_request_upload_urls_missing_files(self):
        status, resp = handlers.request_upload_urls({}, {}, {})
        self.assertEqual(status, 400)
        self.assertIn("error", resp)

    @patch("route_handlers.initialize_batch_stats")
    @patch("storage.put_text")
    def test_upload_batch_files_success(self, mock_put_text, mock_init_stats):
        body = {
            "batch_id": "test-batch-002",
            "files": [
                {"filename": "note1.txt", "content": "Patient clinical text note 1"},
                {"filename": "note2.txt", "content": "Patient clinical text note 2"},
            ],
        }

        status, resp = handlers.upload_batch_files({}, body, {})
        self.assertEqual(status, 200)
        self.assertEqual(resp["batch_id"], "test-batch-002")
        self.assertEqual(resp["uploaded_count"], 2)
        self.assertEqual(resp["status"], "ready")
        self.assertEqual(mock_put_text.call_count, 2)
        mock_init_stats.assert_called_once_with("test-batch-002", 2)

    def test_upload_batch_files_empty(self):
        status, resp = handlers.upload_batch_files({}, {"files": []}, {})
        self.assertEqual(status, 400)
        self.assertIn("error", resp)


if __name__ == "__main__":
    unittest.main()
