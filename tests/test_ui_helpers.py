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


if __name__ == "__main__":
    unittest.main()
