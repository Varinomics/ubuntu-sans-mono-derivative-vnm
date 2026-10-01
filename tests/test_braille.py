"""Braille pattern semantics and equal spacing; visual weight is not certified."""
from __future__ import annotations

import unittest
import unicodedata

from fontTools.pens.ttGlyphPen import TTGlyphPen

import vnm_font as v
from test_vnm_font import box, fixture


def contour_centers(font, name):
    contours = v.contour_data(font["glyf"][name], font["glyf"])
    return sorted(
        ((min(x for x, y in points) + max(x for x, y in points)) / 2,
         (min(y for x, y in points) + max(y for x, y in points)) / 2)
        for points, flags in contours)


class BrailleTests(unittest.TestCase):
    def setUp(self):
        self.baseline = fixture()
        # A deliberately unequal character seam, like the upstream font.
        positions = [(180, 600), (180, 400), (180, 200), (420, 600),
                     (420, 400), (420, 200), (180, 0), (420, 0)]
        names = [v.required(self.baseline, 0x2800 + (1 << bit)) for bit in range(8)]
        for name, (x, y) in zip(names, positions):
            v.install_glyph(self.baseline, name, box(x - 30, y - 30, x + 30, y + 30), 600)
        for pattern in range(256):
            if pattern and pattern & (pattern - 1) == 0:
                continue
            pen = TTGlyphPen(self.baseline["glyf"])
            for bit, name in enumerate(names):
                if pattern & (1 << bit):
                    pen.addComponent(name, (1, 0, 0, 1, 0, 0))
            v.install_glyph(self.baseline, v.required(self.baseline, 0x2800 + pattern),
                            pen.glyph(), 600)
        self.baseline["hmtx"].metrics[v.required(self.baseline, 0x2800)] = (609, 0)
        self.result, self.report = v.build_variant(
            self.baseline, fixture(width=500, stem=60), fixture(width=500, stem=60, donor=True))

    def test_all_patterns_follow_unicode_dot_names(self):
        # The external oracle is the Unicode Braille Patterns naming scheme:
        # https://www.unicode.org/charts/PDF/U2800.pdf
        grid = {"1": (150, 750), "2": (150, 450), "3": (150, 150),
                "4": (450, 750), "5": (450, 450), "6": (450, 150),
                "7": (150, -150), "8": (450, -150)}
        for cp in range(0x2800, 0x2900):
            with self.subTest(codepoint=f"U+{cp:04X}"):
                name = v.required(self.result, cp)
                digits = unicodedata.name(chr(cp)).partition("DOTS-")[2]
                self.assertEqual(contour_centers(self.result, name), sorted(grid[d] for d in digits))
                self.assertEqual(self.result["hmtx"].metrics[name][0], 600)

    def test_spacing_is_equal_within_and_between_characters(self):
        name = v.required(self.result, 0x28FF)
        centers = contour_centers(self.result, name)
        columns = sorted({x for x, y in centers})
        rows    = sorted({y for x, y in centers})
        tiled_columns = columns + [x + 600 for x in columns]
        spacings = [b - a for a, b in zip(tiled_columns, tiled_columns[1:])]
        spacings.extend(b - a for a, b in zip(rows, rows[1:]))
        self.assertEqual(set(spacings), {300})
        self.assertEqual((rows[0] + rows[-1]) / 2, 300)

    def test_dot_outlines_are_only_translated(self):
        for bit in range(8):
            name = v.required(self.result, 0x2800 + (1 << bit))
            old_points, old_ends, old_flags = self.baseline["glyf"][name].getCoordinates(self.baseline["glyf"])
            new_points, new_ends, new_flags = self.result["glyf"][name].getCoordinates(self.result["glyf"])
            self.assertEqual(old_ends, new_ends)
            self.assertEqual(old_flags, new_flags)
            offsets = {(nx - ox, ny - oy) for (ox, oy), (nx, ny) in zip(old_points, new_points)}
            self.assertEqual(len(offsets), 1)

    def test_blank_and_unrelated_glyphs_and_metrics_survive(self):
        blank = v.required(self.result, 0x2800)
        self.assertEqual(self.result["glyf"][blank].numberOfContours, 0)
        self.assertEqual(self.result["hmtx"].metrics[blank][0], 600)
        self.assertEqual(self.result.getGlyphOrder()[:len(self.baseline.getGlyphOrder())],
                         self.baseline.getGlyphOrder())
        validation = v.validate(self.baseline, self.result, self.report)
        self.assertTrue(validation["unchanged_unrelated_outlines"])
        self.assertTrue(validation["unchanged_line_metrics"])


if __name__ == "__main__":
    unittest.main()
