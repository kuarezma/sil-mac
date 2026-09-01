from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from nexus import deletion_engine
from nexus.deletion_engine import execute_deletion_with_live_report, set_dry_run


class DryRunTests(unittest.TestCase):
    def tearDown(self):
        # Never leak the global dry-run toggle into other test modules.
        set_dry_run(False)

    def _run(self, items, log_dir):
        with patch("nexus.deletion_engine.time.sleep"), patch(
            "nexus.deletion_engine.celebrate_freed_space"
        ), patch("nexus.deletion_engine.DELETION_LOG_PATH", str(Path(log_dir) / "log.jsonl")):
            return execute_deletion_with_live_report(items, "Dry Run Testi")

    def test_dry_run_does_not_delete_the_file(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as log_dir:
            target = Path(directory) / "keep_me.bin"
            target.write_bytes(b"x" * 4096)

            set_dry_run(True)
            result = self._run(
                [{"name": "keep_me.bin", "category": "Test", "path": str(target), "size": 999, "type": "file"}],
                log_dir,
            )

            self.assertTrue(target.exists(), "dry-run must never touch the filesystem")
            self.assertEqual(result["results"][0]["status"], "Simülasyon")
            self.assertEqual(result["total_freed"], 4096)

    def test_dry_run_does_not_write_to_the_audit_log(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as log_dir:
            target = Path(directory) / "keep_me.bin"
            target.write_bytes(b"x" * 10)
            log_path = Path(log_dir) / "log.jsonl"

            set_dry_run(True)
            self._run(
                [{"name": "keep_me.bin", "category": "Test", "path": str(target), "size": 10, "type": "file"}],
                log_dir,
            )

            self.assertFalse(log_path.exists(), "a simulated deletion must not be recorded as a real one")

    def test_normal_mode_still_deletes_for_real(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as log_dir:
            target = Path(directory) / "delete_me.bin"
            target.write_bytes(b"x" * 10)

            set_dry_run(False)
            result = self._run(
                [{"name": "delete_me.bin", "category": "Test", "path": str(target), "size": 10, "type": "file"}],
                log_dir,
            )

            self.assertFalse(target.exists())
            self.assertEqual(result["results"][0]["status"], "Başarılı")


if __name__ == "__main__":
    unittest.main()
