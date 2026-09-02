from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from nexus.deletion_engine import execute_deletion_with_live_report


def _run_deletion(items):
    # Redirect the audit log to a throwaway path so running the test suite
    # never writes into the real user's ~/Library/Application Support/Nexus.
    with patch("nexus.deletion_engine.time.sleep"), patch(
        "nexus.deletion_engine.celebrate_freed_space"
    ), tempfile.TemporaryDirectory() as log_dir, patch(
        "nexus.deletion_engine.DELETION_LOG_PATH", str(Path(log_dir) / "deletion_log.jsonl")
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

    @patch("subprocess.run")
    def test_deletes_with_sudo_on_permission_error(self, mock_run):
        mock_run.return_value.returncode = 0
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "root_file.bin"
            target.write_bytes(b"x" * 64)

            with patch("os.remove", side_effect=PermissionError("Permission denied")):
                result = _run_deletion([
                    {"name": "Kök Dosya", "path": str(target), "size": 64, "type": "file"}
                ])
                self.assertEqual(result["total_freed"], 64)
                self.assertEqual(result["results"][0]["status"], "Başarılı")
                mock_run.assert_called_with(["sudo", "rm", "-f", str(target)], check=False, stdout=-3, stderr=-3)
