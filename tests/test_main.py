import unittest
from unittest.mock import patch
from nexus import main as nexus_main
from nexus import deletion_engine

class MainCliTests(unittest.TestCase):
    def tearDown(self):
        deletion_engine.set_dry_run(False)

    @patch("sys.argv", ["sil", "--version"])
    def test_version_flag(self):
        with self.assertRaises(SystemExit) as cm:
            nexus_main.main()
        self.assertEqual(cm.exception.code, 0)

    @patch("sys.argv", ["sil", "--dry-run", "status"])
    @patch("nexus.hardware_dashboard.HardwareDashboard.render")
    @patch("nexus.banner.print_banner")
    def test_dry_run_flag_sets_engine_mode(self, mock_banner, mock_render):
        nexus_main.main()
        self.assertTrue(deletion_engine.DRY_RUN)
        mock_render.assert_called_once()

    @patch("nexus.main.confirm_menu", return_value=False)
    def test_quick_clean_cancel(self, mock_confirm):
        nexus_main._quick_clean()
        mock_confirm.assert_called_once()

    @patch("nexus.main.confirm_menu", return_value=True)
    @patch("nexus.main.SystemCleaner")
    @patch("nexus.main.AIRadar")
    @patch("nexus.main.execute_deletion_with_live_report")
    def test_quick_clean_filters_safe_items(self, mock_exec, mock_ai_cls, mock_sys_cls, mock_confirm):
        mock_sys_cls.return_value.scan.return_value = [{"name": "Trash", "category": "Çöp", "path": "/mock", "size": 100}]
        mock_ai_cls.return_value.scan.return_value = [{"name": "Blob", "category": "Ollama (Yetim)", "path": "/blob", "size": 200}]

        nexus_main._quick_clean()
        mock_exec.assert_called_once()
        args, _ = mock_exec.call_args
        items = args[0]
        self.assertEqual(len(items), 2)
        names = [it["name"] for it in items]
        self.assertIn("Trash", names)
        self.assertIn("Blob", names)

if __name__ == "__main__":
    unittest.main()
