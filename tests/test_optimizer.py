import tempfile
import plistlib
from pathlib import Path
import unittest
from unittest.mock import patch, MagicMock
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

    @patch("subprocess.run")
    def test_purge_ram_elevates_to_sudo(self, mock_run):
        # First call fails (code 1), second call (sudo) succeeds (code 0)
        res_fail = MagicMock(returncode=1)
        res_ok = MagicMock(returncode=0)
        mock_run.side_effect = [res_fail, res_ok]
        self.opt.purge_ram()
        self.assertEqual(mock_run.call_count, 2)
        mock_run.assert_called_with(["sudo", "purge"], check=False)

    @patch("subprocess.run")
    @patch("os.path.exists", return_value=True)
    def test_repair_font_cache(self, mock_exists, mock_run):
        with patch("shutil.rmtree") as mock_rm:
            self.opt.repair_font_cache()
            mock_rm.assert_called_once()

    @patch("subprocess.run")
    def test_refresh_spotlight(self, mock_run):
        mock_run.return_value.stdout = "Indexing enabled."
        self.opt.refresh_spotlight()
        self.assertGreaterEqual(mock_run.call_count, 3)

    @patch("subprocess.run")
    def test_clean_local_snapshots(self, mock_run):
        mock_run.return_value.stdout = "com.apple.TimeMachine.2024-01-01-120000.local"
        self.opt.clean_local_snapshots()
        self.assertEqual(mock_run.call_count, 2)

    @patch("os.path.exists", return_value=True)
    @patch("os.listdir", return_value=["test_socket.sock"])
    @patch("os.path.isfile", return_value=True)
    @patch("os.unlink")
    def test_clean_stale_ipc(self, mock_unlink, mock_isfile, mock_listdir, mock_exists):
        self.opt.clean_stale_ipc()
        mock_unlink.assert_called_once()

    @patch("os.path.exists", return_value=False)
    @patch("subprocess.check_output")
    @patch("psutil.virtual_memory")
    @patch("psutil.swap_memory")
    @patch("psutil.disk_usage")
    def test_get_health_audit(self, mock_disk, mock_swap, mock_vm, mock_chk, mock_exists):
        mock_vm.return_value.total = 16 * (1024**3)
        mock_vm.return_value.used = 8 * (1024**3)
        mock_vm.return_value.available = 8 * (1024**3)
        mock_vm.return_value.percent = 50.0

        mock_swap.return_value.total = 4 * (1024**3)
        mock_swap.return_value.used = 0

        mock_disk.return_value.total = 500 * (1024**3)
        mock_disk.return_value.used = 200 * (1024**3)
        mock_disk.return_value.free = 300 * (1024**3)
        mock_disk.return_value.percent = 40.0

        def fake_chk(cmd, **kwargs):
            if cmd[0] == "pmset" and cmd[2] == "batt":
                return "Now drawing from 'AC Power'\n -InternalBattery-0 (id=123) 85%; AC attached; not charging present: true"
            elif cmd[0] == "ioreg":
                return '"CycleCount" = 120\n"Condition" = "Normal"\n"FullChargeCapacity" = 4500\n"DesignCapacity" = 4500\n'
            elif cmd[0] == "vm_stat":
                return "Mach Virtual Memory Statistics: (page size of 16384 bytes)\nPages free: 3000.\nPages active: 1000.\nPages wired down: 500.\nPages occupied by compressor: 100."
            elif cmd[0] == "pmset" and cmd[2] == "therm":
                return "Note: No thermal warning level has been recorded\nCPU_Scheduler_Limit = 100"
            elif cmd[0] == "tmutil":
                return "Snapshots for disk /:\n"
            return ""

        mock_chk.side_effect = fake_chk

        audit = self.opt.get_health_audit()
        self.assertIsInstance(audit, dict)
        self.assertIn("score", audit)
        self.assertIn("battery", audit)
        self.assertIn("memory", audit)
        self.assertIn("storage", audit)
        self.assertIn("thermal", audit)
        self.assertEqual(audit["battery"]["percent"], 85)
        self.assertEqual(audit["battery"]["cycle_count"], 120)
        self.assertEqual(audit["battery"]["health_percent"], 100.0)
        self.assertGreaterEqual(audit["score"], 90)

    @patch.object(SystemOptimizer, "get_health_audit")
    def test_render_health_audit(self, mock_audit):
        mock_audit.return_value = {
            "battery": {
                "percent": 80, "state": "AC", "health_percent": 95.0,
                "condition": "Normal", "cycle_count": 150
            },
            "memory": {
                "pressure_percent": 45.0, "compressed_gb": 1.2,
                "wired_gb": 2.0, "swap_used_bytes": 0
            },
            "storage": {
                "free_bytes": 200 * (1024**3), "total_bytes": 500 * (1024**3),
                "percent": 60.0, "local_snapshots_count": 0
            },
            "thermal": {
                "status": "Optimal", "throttled": False, "scheduler_limit": 100
            },
            "stability": {
                "recent_crash_count": 0, "top_crashing_apps": []
            },
            "startup": {
                "total_agents": 5, "orphan_agents_count": 0
            },
            "score": 98,
            "status_label": "Mükemmel",
            "status_color": "#34d399",
            "recommendations": ["Sisteminiz harika durumda."]
        }
        self.opt.render_health_audit()

    @patch("nexus.optimizer.confirm_menu", return_value=True)
    @patch.object(SystemOptimizer, "purge_ram")
    @patch.object(SystemOptimizer, "flush_dns")
    @patch.object(SystemOptimizer, "reset_quicklook")
    @patch.object(SystemOptimizer, "rebuild_launchservices")
    @patch.object(SystemOptimizer, "repair_font_cache")
    @patch.object(SystemOptimizer, "restart_audio")
    @patch.object(SystemOptimizer, "refresh_spotlight")
    @patch.object(SystemOptimizer, "clean_local_snapshots")
    @patch.object(SystemOptimizer, "clean_stale_ipc")
    def test_run_full_optimization(self, mock_ipc, mock_snap, mock_spot, mock_aud, mock_font, mock_ls, mock_ql, mock_dns, mock_ram, mock_conf):
        self.opt.run_full_optimization()
        mock_conf.assert_called_once()
        mock_ram.assert_called_once()
        mock_dns.assert_called_once()
        mock_ql.assert_called_once()
        mock_ls.assert_called_once()
        mock_font.assert_called_once()
        mock_aud.assert_called_once()
        mock_spot.assert_called_once()
        mock_snap.assert_called_once()
        mock_ipc.assert_called_once()

    def test_inspect_launch_agents_detects_orphans(self):
        with tempfile.TemporaryDirectory() as d:
            plist_valid = Path(d) / "com.valid.app.plist"
            plist_orphan = Path(d) / "com.orphan.app.plist"

            with open(plist_valid, "wb") as f:
                plistlib.dump({"Label": "com.valid.app", "Program": "/bin/sh"}, f)
            with open(plist_orphan, "wb") as f:
                plistlib.dump({"Label": "com.orphan.app", "Program": "/non/existent/path/xyz"}, f)

            with patch("nexus.optimizer.os.path.exists") as mock_exists:
                def fake_exists(p):
                    if p in [d, "/bin/sh"]:
                        return True
                    if p == "/non/existent/path/xyz":
                        return False
                    return False
                mock_exists.side_effect = fake_exists

                with patch("os.listdir", return_value=["com.valid.app.plist", "com.orphan.app.plist"]), \
                     patch("nexus.optimizer.select_menu", return_value="back"):
                    self.opt.inspect_launch_agents()

    def test_remove_launch_agent_user_and_daemon(self):
        with tempfile.TemporaryDirectory() as d:
            plist_file = Path(d) / "com.test.agent.plist"
            plist_file.write_text("<plist></plist>")

            agent_user = {
                "path": str(plist_file),
                "label": "com.test.agent",
                "scope": "Kullanıcı"
            }
            with patch("subprocess.run") as mock_run:
                res = self.opt.remove_launch_agent(agent_user)
                self.assertTrue(res)
                self.assertFalse(plist_file.exists())
                self.assertGreaterEqual(mock_run.call_count, 1)

    @patch("builtins.input", return_value="")
    @patch("nexus.optimizer.select_menu", side_effect=["clean_select", "back"])
    @patch("nexus.optimizer.confirm_menu", return_value=True)
    def test_inspect_launch_agents_interactive_selection(self, mock_conf, mock_select, mock_input):
        with tempfile.TemporaryDirectory() as d:
            plist_file = Path(d) / "com.test.xquartz.plist"
            plist_file.write_text("<plist></plist>")
            agent = {
                "filename": "com.test.xquartz.plist",
                "path": str(plist_file),
                "label": "com.test.xquartz",
                "scope": "Kullanıcı",
                "program": "/usr/bin/open",
                "exists": True
            }
            with patch.object(SystemOptimizer, "scan_launch_agents", side_effect=[[agent], []]), \
                 patch("nexus.optimizer.checkbox_menu", return_value=[agent]), \
                 patch.object(SystemOptimizer, "remove_launch_agent", return_value=True) as mock_remove:
                self.opt.inspect_launch_agents()
                mock_remove.assert_called_once_with(agent)

    def test_setup_touchid_detects_existing_configuration(self):
        with tempfile.TemporaryDirectory() as d:
            pam_file = Path(d) / "sudo"
            pam_file.write_text("auth       sufficient     pam_tid.so\nauth       required       pam_opendirectory.so\n")
            with patch("nexus.optimizer.os.path.exists", return_value=True), patch("builtins.open", unittest.mock.mock_open(read_data="auth       sufficient     pam_tid.so\n")):
                self.opt.setup_touchid()

if __name__ == "__main__":
    unittest.main()
