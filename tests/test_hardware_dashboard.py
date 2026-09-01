import unittest
from unittest.mock import patch, MagicMock
from nexus.hardware_dashboard import HardwareDashboard

class HardwareDashboardTests(unittest.TestCase):
    def setUp(self):
        self.hd = HardwareDashboard()

    @patch("subprocess.check_output")
    def test_get_system_info(self, mock_sub):
        mock_sub.side_effect = [
            "Apple M3\n",
            "15.0\n",
            "macOS\n",
            " 0:00 up 10:00, 1 user\n"
        ]
        info = self.hd.get_system_info()
        self.assertEqual(info["chip"], "Apple M3")
        self.assertIn("macOS 15.0", info["os_ver"])
        self.assertEqual(info["uptime"], "10:00")

    @patch("subprocess.check_output")
    def test_get_battery_info_discharging(self, mock_sub):
        mock_sub.side_effect = [
            "Now drawing from 'Battery Power'\n -InternalBattery-0 (id=123)\t85%; discharging;\n",
            "Cycle Count: 100\nCondition: Normal\nMaximum Capacity: 95%\n"
        ]
        batt = self.hd.get_battery_info()
        self.assertEqual(batt["percent"], 85)
        self.assertEqual(batt["state"], "Pilde (Deşarj)")
        self.assertFalse(batt["is_charging"])
        self.assertEqual(batt["cycle_count"], "100")
        self.assertIn("Normal", batt["health"])

    @patch("subprocess.check_output")
    def test_get_battery_info_not_charging_on_ac(self, mock_sub):
        mock_sub.side_effect = [
            "Now drawing from 'AC Power'\n -InternalBattery-0 (id=123)\t80%; AC attached; not charging present: true\n",
            "Cycle Count: 190\nCondition: Normal\nMaximum Capacity: %95\n"
        ]
        batt = self.hd.get_battery_info()
        self.assertEqual(batt["percent"], 80)
        self.assertEqual(batt["state"], "AC Adaptöründe (Beklemede)")
        self.assertFalse(batt["is_charging"])

    @patch("subprocess.check_output")
    def test_get_battery_info_charging_active(self, mock_sub):
        mock_sub.side_effect = [
            "Now drawing from 'AC Power'\n -InternalBattery-0 (id=123)\t45%; AC attached; charging present: true\n",
            "Cycle Count: 50\nCondition: Normal\n"
        ]
        batt = self.hd.get_battery_info()
        self.assertEqual(batt["percent"], 45)
        self.assertEqual(batt["state"], "Şarj Oluyor (AC)")
        self.assertTrue(batt["is_charging"])

    @patch("psutil.virtual_memory")
    @patch("psutil.swap_memory")
    @patch("subprocess.check_output")
    def test_get_memory_info_calculates_pressure_with_page_size(self, mock_sub, mock_swap, mock_vm):
        mock_vm.return_value = MagicMock(total=16*1024**3, used=8*1024**3, available=8*1024**3, percent=50.0)
        mock_swap.return_value = MagicMock(total=0, used=0)
        mock_sub.return_value = (
            "Mach Virtual Memory Statistics: (page size of 16384 bytes)\n"
            "Pages free: 10000.\n"
            "Pages active: 20000.\n"
            "Pages inactive: 10000.\n"
            "Pages speculative: 500.\n"
            "Pages wired down: 10000.\n"
            "Pages occupied by compressor: 5000.\n"
        )
        mem = self.hd.get_memory_info()
        self.assertEqual(mem["total"], 16*1024**3)
        self.assertGreater(mem["active_gb"], 0)
        self.assertGreater(mem["pressure"], 0)

if __name__ == "__main__":
    unittest.main()
