import unittest
from rich.text import Text
from nexus.effects import (
    hex_to_rgb, rgb_to_hex, interpolate_color, cyber_gradient, sparkline, neon_badge
)

class EffectsTests(unittest.TestCase):
    def test_hex_rgb_conversions(self):
        rgb = hex_to_rgb("#ff0000")
        self.assertEqual(rgb, (255, 0, 0))
        self.assertEqual(rgb_to_hex(255, 0, 0), "#ff0000")

    def test_interpolate_color(self):
        mid = interpolate_color("#000000", "#ffffff", 0.5)
        self.assertEqual(mid, "#7f7f7f")

    def test_cyber_gradient_returns_rich_text(self):
        grad = cyber_gradient("SIL OPTIMIZER")
        self.assertIsInstance(grad, Text)
        self.assertEqual(grad.plain, "SIL OPTIMIZER")

    def test_sparkline_empty(self):
        self.assertEqual(sparkline([]), "")

    def test_sparkline_equal_min_max(self):
        res = sparkline([50, 50, 50])
        self.assertEqual(len(res), 3)

    def test_sparkline_distribution(self):
        res = sparkline([0, 50, 100])
        self.assertEqual(len(res), 3)
        self.assertEqual(res[0], " ")
        self.assertEqual(res[-1], "█")

    def test_neon_badge_formatting(self):
        badge = neon_badge("PRO", bg="#00f0ff")
        self.assertIn("PRO", badge)
        self.assertIn("#00f0ff", badge)

if __name__ == "__main__":
    unittest.main()
