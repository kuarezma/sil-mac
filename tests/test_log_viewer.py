from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from nexus.log_viewer import _read_log_entries


class ReadLogEntriesTests(unittest.TestCase):
    def test_missing_log_file_returns_empty_list(self):
        with tempfile.TemporaryDirectory() as d:
            with patch("nexus.log_viewer.DELETION_LOG_PATH", str(Path(d) / "missing.jsonl")):
                self.assertEqual(_read_log_entries(), [])

    def test_parses_valid_lines_and_skips_corrupt_ones(self):
        with tempfile.TemporaryDirectory() as d:
            log_path = Path(d) / "log.jsonl"
            log_path.write_text(
                '{"name": "a.txt", "size": 10}\n'
                "not valid json\n"
                '{"name": "b.txt", "size": 20}\n'
            )
            with patch("nexus.log_viewer.DELETION_LOG_PATH", str(log_path)):
                entries = _read_log_entries()

            self.assertEqual(len(entries), 2)
            self.assertEqual(entries[0]["name"], "a.txt")
            self.assertEqual(entries[1]["name"], "b.txt")


if __name__ == "__main__":
    unittest.main()
