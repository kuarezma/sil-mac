import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
from nexus.optimizer import SystemOptimizer

class SystemOptimizerTests(unittest.TestCase):
    def setUp(self):
        self.opt = SystemOptimizer()

    @patch("subprocess.run")
    def test_flush_dns(self, mock_run):
        self.opt.flush_dns()
        self.assertEqual(mock_run.call_count, 2)

    @patch("subprocess.run")
    def test_reset_quicklook(self, mock_run):
        self.opt.reset_quicklook()
        self.assertEqual(mock_run.call_count, 2)

    @patch("subprocess.run")
    def test_restart_audio(self, mock_run):
        self.opt.restart_audio()
        mock_run.assert_called_once_with(["killall", "coreaudiod"], check=False)

    @patch("subprocess.run")
    def test_purge_ram(self, mock_run):
        mock_run.return_value.returncode = 0
        self.opt.purge_ram()
        mock_run.assert_called_once()

    def test_setup_touchid_detects_existing_configuration(self):
        with tempfile.TemporaryDirectory() as d:
            pam_file = Path(d) / "sudo"
            pam_file.write_text("auth       sufficient     pam_tid.so\nauth       required       pam_opendirectory.so\n")
            with patch("nexus.optimizer.os.path.exists", return_value=True), patch("builtins.open", unittest.mock.mock_open(read_data="auth       sufficient     pam_tid.so\n")):
                self.opt.setup_touchid()

if __name__ == "__main__":
    unittest.main()
