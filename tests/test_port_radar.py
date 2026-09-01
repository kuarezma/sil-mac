import unittest

from nexus.port_radar import is_protected_pid


class IsProtectedPidTests(unittest.TestCase):
    """Guards against SIGKILL'ing Nexus itself, its parent shell, PID 0/1,
    or macOS processes whose death takes the session/machine down."""

    def test_self_pid_is_protected(self):
        self.assertTrue(is_protected_pid(100, current_pid=100, parent_pid=50, proc_name="python"))

    def test_parent_shell_pid_is_protected(self):
        self.assertTrue(is_protected_pid(50, current_pid=100, parent_pid=50, proc_name="zsh"))

    def test_pid_zero_and_one_are_protected(self):
        self.assertTrue(is_protected_pid(0, current_pid=100, parent_pid=50, proc_name="kernel_task"))
        self.assertTrue(is_protected_pid(1, current_pid=100, parent_pid=50, proc_name="launchd"))

    def test_critical_system_process_names_are_protected(self):
        for name in ["launchd", "kernel_task", "WindowServer", "LoginWindow"]:
            self.assertTrue(
                is_protected_pid(999, current_pid=100, parent_pid=50, proc_name=name),
                msg=f"{name} should be protected regardless of PID",
            )

    def test_ordinary_process_is_not_protected(self):
        self.assertFalse(is_protected_pid(4242, current_pid=100, parent_pid=50, proc_name="Safari"))


if __name__ == "__main__":
    unittest.main()
