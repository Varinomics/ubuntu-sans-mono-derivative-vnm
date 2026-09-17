"""Directional-arrow regression tests for U+2190/U+2191/U+2192/U+2193."""
from __future__ import annotations

import unittest

import vnm_font as v
from test_vnm_font import fixture

ARROWS = {0x2190: "left", 0x2191: "up", 0x2192: "right", 0x2193: "down"}


class DirectionalArrowTests(unittest.TestCase):
    def setUp(self):
        self.upstream = fixture(width=600, stem=72)
        self.original = fixture(width=500, stem=60)
        self.bront = fixture(width=500, stem=60, donor=True)

    def test_directional_arrows_are_in_keyboard_set(self):
        for cp in ARROWS:
            self.assertIn(cp, v.KEYBOARD)

    def test_geometry_is_nonempty_and_within_cell(self):
        for cp in ARROWS:
            with self.subTest(cp=hex(cp)):
                g = v.keyboard_glyph(cp, 560, 700, 65)
                self.assertGreater(g.numberOfContours, 0)
                self.assertGreaterEqual(g.xMin, 0)
                self.assertLessEqual(g.xMax, 560)
                self.assertGreaterEqual(g.yMin, 0)
                self.assertLessEqual(g.yMax, 700)

    def test_full_font_build_adds_distinct_arrow_mappings(self):
        result, report = v.build_variant(self.upstream, self.original, self.bront)
        mapped = {cp: v.required(result, cp) for cp in ARROWS}
        self.assertEqual(len(set(mapped.values())), 4)
        report_pairs = {(x["codepoint"], x["glyph"]) for x in report["added_glyphs"]}
        for cp, name in mapped.items():
            self.assertIn((f"U+{cp:04X}", name), report_pairs)

    def test_existing_arrow_not_overwritten(self):
        g = v.keyboard_glyph(0x2190, 560, 700, 65)
        v.add_mapping(self.upstream, 0x2190, "existingLeftArrow", g, 600)
        result, report = v.build_variant(self.upstream, self.original, self.bront)
        self.assertEqual(v.required(result, 0x2190), "existingLeftArrow")
        self.assertNotIn("U+2190", [x["codepoint"] for x in report["added_glyphs"]])
