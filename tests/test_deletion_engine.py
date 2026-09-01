from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from nexus.deletion_engine import execute_deletion_with_live_report


def _run_deletion(items):
    with patch("nexus.deletion_engine.time.sleep"), patch(
        "nexus.deletion_engine.celebrate_freed_space"
    ):
        return execute_deletion_with_live_report(items, "Test temizliği")


class DeletionEngineTests(unittest.TestCase):
    def test_deletes_file_and_reports_actual_reclaimed_size(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "cache.bin"
            target.write_bytes(b"x" * 32)

            result = _run_deletion([
                {"name": "Önbellek", "path": str(target), "size": 999, "type": "file"}
            ])

            self.assertFalse(target.exists())
            self.assertEqual(result["total_freed"], 32)
            self.assertEqual(result["results"][0]["status"], "Başarılı")
            self.assertEqual(result["results"][0]["size"], 32)

    def test_missing_path_is_not_reported_as_freed(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "gone.bin"

            result = _run_deletion([
                {"name": "Eksik", "path": str(missing), "size": 128, "type": "file"}
            ])

            self.assertEqual(result["total_freed"], 0)
            self.assertEqual(result["results"][0]["status"], "Başarısız")
            self.assertIn("bulunamadı", result["results"][0]["error"])

    def test_empty_path_is_rejected(self):
        result = _run_deletion([
            {"name": "Geçersiz", "path": "", "size": 128, "type": "file"}
        ])

        self.assertEqual(result["total_freed"], 0)
        self.assertEqual(result["results"][0]["status"], "Başarısız")
        self.assertIn("Geçerli", result["results"][0]["error"])
