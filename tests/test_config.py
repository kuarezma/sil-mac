import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from nexus import config as nexus_config


class ConfigTests(unittest.TestCase):
    def setUp(self):
        nexus_config._cached_config = None

    def tearDown(self):
        nexus_config._cached_config = None

    def test_missing_config_file_returns_defaults(self):
        with tempfile.TemporaryDirectory() as d:
            with patch("nexus.config.CONFIG_PATH", str(Path(d) / "missing.json")):
                self.assertEqual(
                    nexus_config.get("dev_cleaner.artifact_threshold_mb"), 5
                )

    def test_user_value_overrides_default_for_that_key_only(self):
        with tempfile.TemporaryDirectory() as d:
            config_path = Path(d) / "config.json"
            config_path.write_text(json.dumps({"dev_cleaner": {"artifact_threshold_mb": 100}}))

            with patch("nexus.config.CONFIG_PATH", str(config_path)):
                self.assertEqual(nexus_config.get("dev_cleaner.artifact_threshold_mb"), 100)
                # sibling default key must survive the merge untouched
                self.assertEqual(nexus_config.get("dev_cleaner.cache_threshold_mb"), 1)

    def test_malformed_json_falls_back_to_defaults_without_crashing(self):
        with tempfile.TemporaryDirectory() as d:
            config_path = Path(d) / "config.json"
            config_path.write_text("{not valid json")

            with patch("nexus.config.CONFIG_PATH", str(config_path)):
                self.assertEqual(
                    nexus_config.get("dev_cleaner.artifact_threshold_mb"), 5
                )

    def test_unknown_key_returns_the_given_default(self):
        with tempfile.TemporaryDirectory() as d:
            with patch("nexus.config.CONFIG_PATH", str(Path(d) / "missing.json")):
                self.assertEqual(nexus_config.get("nonexistent.key", "fallback"), "fallback")

    def test_write_default_config_if_missing_creates_valid_json_once(self):
        with tempfile.TemporaryDirectory() as d:
            config_path = Path(d) / "sub" / "config.json"
            with patch("nexus.config.CONFIG_PATH", str(config_path)):
                created = nexus_config.write_default_config_if_missing()
                self.assertTrue(created)
                self.assertTrue(config_path.exists())
                data = json.loads(config_path.read_text())
                self.assertIn("dev_cleaner", data)

                # second call must not overwrite / must report False
                created_again = nexus_config.write_default_config_if_missing()
                self.assertFalse(created_again)

    def test_expand_paths_expands_tilde(self):
        expanded = nexus_config.expand_paths(["~/Desktop", "/absolute/path"])
        self.assertTrue(expanded[0].startswith("/"))
        self.assertNotIn("~", expanded[0])
        self.assertEqual(expanded[1], "/absolute/path")


if __name__ == "__main__":
    unittest.main()
