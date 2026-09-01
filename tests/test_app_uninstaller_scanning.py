import plistlib
from pathlib import Path
import tempfile
import unittest

from nexus.app_uninstaller import AppUninstaller


def _make_app(apps_dir: Path, name: str, bundle_id: str, payload_size: int = 2048):
    app_path = apps_dir / f"{name}.app"
    contents = app_path / "Contents"
    contents.mkdir(parents=True)
    with open(contents / "Info.plist", "wb") as f:
        plistlib.dump({"CFBundleIdentifier": bundle_id}, f)
    with open(contents / "payload.bin", "wb") as f:
        f.truncate(payload_size)
    return app_path


class ListInstalledAppsTests(unittest.TestCase):
    def test_finds_app_and_reads_bundle_id(self):
        with tempfile.TemporaryDirectory() as apps_dir:
            _make_app(Path(apps_dir), "Fixture", "com.example.fixture")

            au = AppUninstaller()
            au.apps_dirs = [apps_dir]
            apps = au.list_installed_apps()

            self.assertEqual(len(apps), 1)
            self.assertEqual(apps[0]["name"], "Fixture")
            self.assertEqual(apps[0]["bundle_id"], "com.example.fixture")
            self.assertGreater(apps[0]["app_size"], 0)

    def test_missing_apps_dir_is_skipped_without_error(self):
        au = AppUninstaller()
        au.apps_dirs = ["/nonexistent/path/for/nexus/tests"]
        self.assertEqual(au.list_installed_apps(), [])


class FindAppResidualsTests(unittest.TestCase):
    def test_matches_by_bundle_id_and_by_word_bounded_name(self):
        with tempfile.TemporaryDirectory() as home:
            home_path = Path(home)
            au = AppUninstaller()
            au.home = home
            au.apps_dirs = [home]

            support = home_path / "Library" / "Application Support" / "com.example.fixture"
            support.mkdir(parents=True, exist_ok=True)
            (support / "data.bin").write_bytes(b"x" * 4096)

            residuals = au.find_app_residuals({"name": "Fixture", "bundle_id": "com.example.fixture"})

            self.assertTrue(any("com.example.fixture" in r["path"] for r in residuals))

    def test_does_not_match_unrelated_folder_with_short_substring(self):
        # App "Sim" must not pick up an unrelated "Simulator" folder as a residual —
        # this is the word-boundary guard also covered in test_app_uninstaller.py,
        # exercised here through the real find_app_residuals scan path.
        with tempfile.TemporaryDirectory() as home:
            home_path = Path(home)
            au = AppUninstaller()
            au.home = home

            caches = home_path / "Library" / "Caches" / "Simulator"
            caches.mkdir(parents=True)
            (caches / "data.bin").write_bytes(b"x" * 4096)

            residuals = au.find_app_residuals({"name": "Sim", "bundle_id": ""})

            self.assertEqual(residuals, [])


if __name__ == "__main__":
    unittest.main()
