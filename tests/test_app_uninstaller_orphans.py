import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
from nexus.app_uninstaller import AppUninstaller

class AppUninstallerOrphansTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        self.au = AppUninstaller()
        self.au.home = str(self.home)
        self.au.apps_dirs = [str(self.home / "Applications")]

    def tearDown(self):
        self.tmp.cleanup()

    def test_scan_orphans_ignores_whitelisted_and_installed(self):
        app_support = self.home / "Library" / "Application Support"
        app_support.mkdir(parents=True)

        # 1. System whitelisted item
        apple_dir = app_support / "com.apple.Safari"
        apple_dir.mkdir()
        (apple_dir / "data.bin").write_bytes(b"x" * (5 * 1024 * 1024))

        # 2. Installed app directory (Simulated Installed App)
        apps_dir = self.home / "Applications"
        apps_dir.mkdir(parents=True)
        my_app = apps_dir / "InstalledTool.app"
        my_app.mkdir()

        installed_residual = app_support / "InstalledTool"
        installed_residual.mkdir()
        (installed_residual / "cache.bin").write_bytes(b"x" * (5 * 1024 * 1024))

        # 3. True orphan directory
        orphan_dir = app_support / "OldDeletedApp"
        orphan_dir.mkdir()
        (orphan_dir / "data.bin").write_bytes(b"x" * (5 * 1024 * 1024))

        with patch("nexus.config.get", return_value=2): # 2MB threshold
            orphans = self.au.scan_orphans()
            orphan_names = [o["name"] for o in orphans]
            self.assertIn("OldDeletedApp", orphan_names)
            self.assertNotIn("com.apple.Safari", orphan_names)
            self.assertNotIn("InstalledTool", orphan_names)

if __name__ == "__main__":
    unittest.main()
