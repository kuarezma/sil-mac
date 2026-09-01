import os
from pathlib import Path
import tempfile
import unittest

from nexus.dev_cleaner import DevCleaner


def _make_dir_with_size(path: Path, size_bytes: int):
    path.mkdir(parents=True, exist_ok=True)
    with open(path / "payload.bin", "wb") as f:
        f.truncate(size_bytes)


class ScanProjectArtifactsTests(unittest.TestCase):
    """Regression coverage for scan_project_artifacts: node_modules/venv/.venv
    are listed in BOTH target_names (things to detect) and ignore_dirs
    (things to stop recursing into). A previous ordering bug applied the
    ignore-list filter before the target-name check, which silently removed
    these directories from `dirs` before they could ever be matched —
    meaning the tool's headline feature (finding node_modules) never fired."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.dc = DevCleaner()

    def tearDown(self):
        self.tmp.cleanup()

    def test_finds_node_modules_despite_also_being_in_ignore_dirs(self):
        _make_dir_with_size(self.root / "myproj" / "node_modules", 6 * 1024 * 1024)

        found = self.dc.scan_project_artifacts([str(self.root)])

        names = [f["name"] for f in found]
        self.assertIn("myproj/node_modules", names)
        self.assertEqual(found[0]["category"], "Node.js Modules")

    def test_finds_dot_venv_and_venv_despite_also_being_in_ignore_dirs(self):
        _make_dir_with_size(self.root / "proj_a" / ".venv", 6 * 1024 * 1024)
        _make_dir_with_size(self.root / "proj_b" / "venv", 6 * 1024 * 1024)

        found = self.dc.scan_project_artifacts([str(self.root)])

        names = {f["name"] for f in found}
        self.assertIn("proj_a/.venv", names)
        self.assertIn("proj_b/venv", names)

    def test_ignores_artifacts_below_the_5mb_threshold(self):
        _make_dir_with_size(self.root / "myproj" / "node_modules", 1024)

        found = self.dc.scan_project_artifacts([str(self.root)])

        self.assertEqual(found, [])

    def test_does_not_descend_more_than_two_levels_deep(self):
        # base_dir/g1/g2/proj/node_modules -> root rel "g1/g2/proj" has 3
        # path components, past the depth cutoff, so it must not be found.
        _make_dir_with_size(
            self.root / "g1" / "g2" / "proj" / "node_modules", 6 * 1024 * 1024
        )

        found = self.dc.scan_project_artifacts([str(self.root)])

        self.assertEqual(found, [])

    def test_finds_artifact_at_two_levels_deep(self):
        # base_dir/group/proj/node_modules -> root rel "group/proj" (2
        # components) is still within the allowed depth.
        _make_dir_with_size(
            self.root / "group" / "proj" / "node_modules", 6 * 1024 * 1024
        )

        found = self.dc.scan_project_artifacts([str(self.root)])

        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["name"], "proj/node_modules")

    def test_missing_scan_dir_is_skipped_without_error(self):
        found = self.dc.scan_project_artifacts([str(self.root / "does_not_exist")])
        self.assertEqual(found, [])


class ScanGlobalCachesTests(unittest.TestCase):
    def test_only_reports_known_caches_present_and_over_threshold(self):
        with tempfile.TemporaryDirectory() as home:
            dc = DevCleaner()
            dc.home = home

            npm_cache = Path(home) / ".npm" / "_cacache"
            _make_dir_with_size(npm_cache, 2 * 1024 * 1024)  # > 1MB threshold

            pip_cache = Path(home) / "Library" / "Caches" / "pip"
            _make_dir_with_size(pip_cache, 10)  # under threshold

            found = dc.scan_global_caches()

            categories = {f["category"]: f["name"] for f in found}
            self.assertIn("Node.js", categories)
            self.assertEqual(categories["Node.js"], "npm Cache")
            self.assertNotIn("Python", categories)


if __name__ == "__main__":
    unittest.main()
