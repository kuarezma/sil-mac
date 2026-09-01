import tempfile
from pathlib import Path
import unittest
from nexus.system_cleaner import SystemCleaner

class SystemCleanerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        self.cleaner = SystemCleaner()
        self.cleaner.home = str(self.home)

    def tearDown(self):
        self.tmp.cleanup()

    def test_scans_user_caches_and_trash(self):
        caches = self.home / "Library" / "Caches" / "test_cache"
        caches.mkdir(parents=True)
        (caches / "cache.db").write_bytes(b"x" * (2 * 1024 * 1024))

        trash = self.home / ".Trash"
        trash.mkdir(parents=True)
        (trash / "old_file.txt").write_bytes(b"y" * (3 * 1024 * 1024))

        items = self.cleaner.scan()
        categories = {it["category"]: it for it in items}
        self.assertIn("Sistem", categories)
        self.assertIn("Çöp", categories)

    def test_scans_downloaded_installers(self):
        downloads = self.home / "Downloads"
        downloads.mkdir(parents=True)
        installer = downloads / "AppInstaller.dmg"
        with open(installer, "wb") as f:
            f.truncate(10 * 1024 * 1024)

        items = self.cleaner.scan()
        installer_items = [it for it in items if it["category"] == "İndirilenler"]
        self.assertEqual(len(installer_items), 1)
        self.assertEqual(installer_items[0]["name"], "Yükleyici: AppInstaller.dmg")
        self.assertEqual(installer_items[0]["type"], "file")

if __name__ == "__main__":
    unittest.main()
