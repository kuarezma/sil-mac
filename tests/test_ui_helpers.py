import unittest

from nexus.ui_helpers import create_header, C_CYAN, C_EMERALD, C_AMBER
from nexus.menu_helpers import format_menu_item


class CreateHeaderTierTests(unittest.TestCase):
    def test_default_tier_is_cyan(self):
        panel = create_header("Title", "Subtitle", "🧹")
        self.assertEqual(panel.border_style, C_CYAN)

    def test_safe_tier_is_emerald(self):
        panel = create_header("Title", "Subtitle", "⚡", tier="safe")
        self.assertEqual(panel.border_style, C_EMERALD)

    def test_caution_tier_is_amber(self):
        panel = create_header("Title", "Subtitle", "📡", tier="caution")
        self.assertEqual(panel.border_style, C_AMBER)

    def test_unknown_tier_falls_back_to_cyan(self):
        panel = create_header("Title", "Subtitle", "🧹", tier="nonexistent")
        self.assertEqual(panel.border_style, C_CYAN)


class FormatMenuItemTests(unittest.TestCase):
    """InquirerPy Choice names are rendered as plain text, not Rich markup —
    embedding [color]...[/color] tags here would print literal brackets
    instead of coloring anything. This guards against ever reintroducing
    Rich-style markup into a Choice label."""

    def test_output_contains_no_rich_style_markup(self):
        text = format_menu_item("🤖", "AI Radar", "some description")
        self.assertNotIn("[/", text)

    def test_title_and_description_are_present(self):
        text = format_menu_item("🤖", "AI Radar", "some description")
        self.assertIn("AI Radar", text)
        self.assertIn("some description", text)


import os
import tempfile
from pathlib import Path
from nexus.ui_helpers import (
    format_bytes, create_gauge, get_path_size, pad_visual, truncate_visual,
    C_RED
)

class FormatBytesTests(unittest.TestCase):
    def test_none_and_negative_returns_zero_bytes(self):
        self.assertEqual(format_bytes(None), "0 B")
        self.assertEqual(format_bytes(-50), "0 B")

    def test_exact_bytes(self):
        self.assertEqual(format_bytes(0), "0 B")
        self.assertEqual(format_bytes(512), "512 B")
        self.assertEqual(format_bytes(1023), "1023 B")

    def test_kilobytes_and_megabytes(self):
        self.assertEqual(format_bytes(1024), "1.0 KB")
        self.assertEqual(format_bytes(1024 * 1024), "1.0 MB")
        self.assertEqual(format_bytes(1536 * 1024), "1.5 MB")

    def test_gigabytes_and_terabytes(self):
        self.assertEqual(format_bytes(1024 * 1024 * 1024), "1.00 GB")
        self.assertEqual(format_bytes(1024 * 1024 * 1024 * 1024), "1.00 TB")

    def test_nan_and_inf(self):
        self.assertEqual(format_bytes(float("nan")), "0 B")
        self.assertEqual(format_bytes(float("inf")), "0 B")

class CreateGaugeTests(unittest.TestCase):
    def test_zero_percentage(self):
        res = create_gauge(0.0, width=10)
        self.assertIn("░" * 10, res)
        self.assertIn("0.0%", res)

    def test_fifty_percentage(self):
        res = create_gauge(50.0, width=10)
        self.assertIn("█" * 5 + "░" * 5, res)
        self.assertIn("50.0%", res)

    def test_one_hundred_percentage(self):
        res = create_gauge(100.0, width=10)
        self.assertIn("█" * 10, res)
        self.assertIn("100.0%", res)
        self.assertIn(C_RED, res)

    def test_nan_percentage_defaults_to_zero(self):
        res = create_gauge(float("nan"), width=10)
        self.assertIn("0.0%", res)

class VisualPaddingAndTruncateTests(unittest.TestCase):
    def test_pad_visual_ascii(self):
        res = pad_visual("test", 10)
        self.assertEqual(res, "test      ")
        self.assertEqual(len(res), 10)

    def test_truncate_visual(self):
        res = truncate_visual("Hello World", 5)
        self.assertTrue(res.endswith("…"))
        self.assertLessEqual(len(res), 6)

class GetPathSizeTests(unittest.TestCase):
    def test_missing_path_returns_zero(self):
        self.assertEqual(get_path_size("/nonexistent/file/path"), 0)

    def test_single_file_size(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "sample.bin"
            f.write_bytes(b"a" * 1024)
            self.assertEqual(get_path_size(str(f)), 1024)

    def test_directory_tree_size(self):
        with tempfile.TemporaryDirectory() as d:
            sub = Path(d) / "sub"
            sub.mkdir()
            (sub / "f1.bin").write_bytes(b"a" * 500)
            (sub / "f2.bin").write_bytes(b"b" * 300)
            self.assertEqual(get_path_size(d), 800)


if __name__ == "__main__":
    unittest.main()
