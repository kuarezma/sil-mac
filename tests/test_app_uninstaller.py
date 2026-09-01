import unittest

from nexus.app_uninstaller import AppUninstaller


class NameMatchesTests(unittest.TestCase):
    """AppUninstaller._name_matches guards residual-file matching. A loose
    substring match here would let an unrelated app's residuals be flagged
    for deletion when uninstalling something else (e.g. app "Sim" matching
    the unrelated folder "Simulator")."""

    def test_exact_match(self):
        self.assertTrue(AppUninstaller._name_matches("sim", "sim"))

    def test_bundle_style_boundary_match(self):
        self.assertTrue(AppUninstaller._name_matches("com.sim.app", "sim"))
        self.assertTrue(AppUninstaller._name_matches("sim.plist", "sim"))
        self.assertTrue(AppUninstaller._name_matches("group.sim", "sim"))

    def test_rejects_substring_inside_a_longer_word(self):
        self.assertFalse(AppUninstaller._name_matches("simulator support", "sim"))
        self.assertFalse(AppUninstaller._name_matches("mysimapp", "sim"))
        self.assertFalse(AppUninstaller._name_matches("similarity", "sim"))

    def test_case_is_pre_lowered_by_caller_not_by_helper(self):
        # The helper assumes both args are already lowercased (as callers do).
        self.assertFalse(AppUninstaller._name_matches("SIMULATOR", "sim"))


if __name__ == "__main__":
    unittest.main()
