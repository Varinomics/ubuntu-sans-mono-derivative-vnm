"""U+23CE regression tests: real procedural outline, synthetic host fonts.

These tests do not certify a complete Ubuntu/Bront build or platform rendering.
"""
from __future__ import annotations

import io
import unittest

from fontTools.pens.pointInsidePen import PointInsidePen
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

import vnm_font as v
from test_vnm_font import fixture


CP = 0x23CE


def filled(glyph, x, y):
    pen = PointInsidePen(None, (x, y), evenOdd=False)
    glyph.draw(pen, None)
    return pen.getResult()


def saved(font):
    data = io.BytesIO()
    font.save(data)
    return data.getvalue()


class ReturnSymbolTests(unittest.TestCase):
    def setUp(self):
        self.upstream = fixture(width=600, stem=72)
        self.original = fixture(width=500, stem=60)
        self.bront = fixture(width=500, stem=60, donor=True)

    def build(self, **kwargs):
        return v.build_variant(self.upstream, self.original, self.bront, **kwargs)

    def test_explicit_keyboard_set_includes_u23ce_without_aliases(self):
        expected = {0x232B, 0x2326, 0x21B5, 0x21E5, 0x21E4, 0x21B9,
                    0x21E7, 0x21E9, 0x21EA, 0x2386, 0x23CE,
                    0x2190, 0x2191, 0x2192, 0x2193}
        self.assertEqual(set(v.KEYBOARD), expected)
        self.assertEqual(len(v.KEYBOARD), len(expected))
        result, report = self.build()
        name = v.required(result, CP)
        self.assertEqual(name, "vnm.uni23CE")
        self.assertIn("Version 1.103", result["name"].getDebugName(5))
        self.assertIn("vnm 0.1.2", result["name"].getDebugName(5))
        self.assertNotEqual(name, v.required(result, 0x21B5))
        self.assertNotEqual(name, v.required(result, 0x2386))
        for other in (0x21B5, 0x2386):
            self.assertNotEqual(v.outline_signature(result, name),
                                v.outline_signature(result, v.required(result, other)))
        for table in result["cmap"].tables:
            if table.isUnicode() and table.format in (4, 12):
                self.assertEqual(table.cmap[CP], name)
        entry = next(x for x in report["added_glyphs"] if x["codepoint"] == "U+23CE")
        self.assertEqual(entry["glyph"], name)
        self.assertEqual(result["hmtx"].metrics[name][0], 600)
        self.assertGreaterEqual(result.getGlyphID(name), len(self.upstream.getGlyphOrder()))

    def test_two_opposite_winding_contours_form_a_real_hole(self):
        glyph = v.keyboard_glyph(CP, 560, 700, 65)
        self.assertEqual(glyph.numberOfContours, 2)
        contours = v.contour_data(glyph, None)
        areas = []
        for points, flags in contours:
            self.assertTrue(all(f & 1 for f in flags))
            areas.append(sum(x*y2-x2*y for (x,y),(x2,y2) in
                             zip(points, points[1:]+points[:1])))
        self.assertLess(areas[0], 0)  # Clockwise exterior.
        self.assertGreater(areas[1], 0)  # Counter-clockwise hole.
        self.assertGreater(abs(areas[0]), abs(areas[1]))
        # Hollow head, horizontal arm, elbow and upright tail.
        for point in ((168,259), (308,259), (442,259), (442,504)):
            with self.subTest(hole=point):
                self.assertFalse(filled(glyph, *point))
        # The surrounding arrow is ink, and there is no enclosing keycap box.
        for point in ((50,259), (308,198), (505,504), (442,620)):
            with self.subTest(ink=point):
                self.assertTrue(filled(glyph, *point))
        for point in ((0,259), (560,259), (308,546), (30,620)):
            with self.subTest(outside=point):
                self.assertFalse(filled(glyph, *point))

    def test_geometry_survives_different_metrics(self):
        for width,cap,stem in ((400,900,30), (560,700,65), (600,693,90), (720,620,120)):
            with self.subTest(width=width,cap=cap,stem=stem):
                g = v.keyboard_glyph(CP, width, cap, stem)
                self.assertEqual(g.numberOfContours, 2)
                self.assertGreaterEqual(g.xMin, 0)
                self.assertLessEqual(g.xMax, width)
                self.assertGreaterEqual(g.yMin, 0)
                self.assertLessEqual(g.yMax, cap)
                tail_center = .92*width-min(.14*width,.105*cap)
                for point in ((.30*width,.37*cap), (.55*width,.37*cap),
                              (tail_center,.37*cap), (tail_center,.72*cap)):
                    self.assertFalse(filled(g, *point), point)
                self.assertTrue(filled(g, .90*width, .72*cap))

    def test_bad_metrics_are_rejected(self):
        for dimensions in ((0,700,65), (560,-1,65), (560,700,0),
                           (float("inf"),700,65), (560,float("nan"),65)):
            with self.subTest(dimensions=dimensions):
                with self.assertRaisesRegex(ValueError, "finite and positive"):
                    v.keyboard_glyph(CP, *dimensions)

    def test_hollow_outline_survives_full_font_roundtrip(self):
        result, report = self.build()
        before = v.outline_signature(result, v.required(result, CP))
        with TTFont(io.BytesIO(saved(result))) as loaded:
            self.assertEqual(v.outline_signature(loaded, v.required(loaded, CP)), before)
            check = v.validate(self.upstream, loaded, report)
            self.assertTrue(check["extra_symbols"]["U+23CE"])
            self.assertEqual(loaded["glyf"][v.required(loaded, CP)].numberOfContours, 2)

    def test_existing_upstream_return_symbol_is_preserved(self):
        existing = v.keyboard_glyph(CP, 600, 700, 72)
        v.add_mapping(self.upstream, CP, "nativeReturn", existing, 600)
        before = v.outline_signature(self.upstream, "nativeReturn")
        result, report = self.build()
        self.assertEqual(v.required(result, CP), "nativeReturn")
        self.assertEqual(v.outline_signature(result, "nativeReturn"), before)
        self.assertNotIn("U+23CE", [x["codepoint"] for x in report["added_glyphs"]])
        self.assertTrue(v.validate(self.upstream, result, report)["extra_symbols"]["U+23CE"])

    def test_no_keyboard_disables_the_new_addition(self):
        result, report = self.build(keyboard=False)
        self.assertNotIn(CP, v.cmap(result))
        self.assertNotIn("U+23CE", [x["codepoint"] for x in report["added_glyphs"]])
        v.validate(self.upstream, result, report, keyboard=False)

    def test_missing_return_mapping_fails_validation(self):
        result, report = self.build()
        for table in result["cmap"].tables:
            if hasattr(table, "cmap"):
                table.cmap.pop(CP, None)
        with self.assertRaisesRegex(ValueError, "U\\+23CE"):
            v.validate(self.upstream, result, report)

    def test_direct_freetype_render_is_hollow(self):
        result, _ = self.build()
        data = saved(result)
        face = ImageFont.truetype(io.BytesIO(data), 1000, layout_engine=ImageFont.Layout.BASIC)
        image = Image.new("L", (660,800), 255)
        draw = ImageDraw.Draw(image)
        draw.text((30,740), chr(CP), font=face, fill=0, anchor="ls")
        # At 1000 ppem, the fixture's font-unit coordinates equal pixels.
        def pixel(x,y):
            return image.getpixel((round(x+30),round(740-y)))
        for point in ((180,259), (330,259), (478,259), (478,504)):
            self.assertGreaterEqual(pixel(*point), 250, point)
        for point in ((54,259), (330,198), (540,504), (478,620)):
            self.assertLessEqual(pixel(*point), 5, point)
        for size in (16,20,24,32,48):
            small = ImageFont.truetype(io.BytesIO(data), size, layout_engine=ImageFont.Layout.BASIC)
            self.assertIsNotNone(small.getmask(chr(CP)).getbbox())
            # BASIC layout grid-fits advances to whole pixels; compare with
            # the same host font's H instead of demanding fractional pixels.
            self.assertEqual(small.getlength(chr(CP)), small.getlength("H"))
            self.assertAlmostEqual(small.getlength(chr(CP)), .6*size, delta=.51)

    def test_return_symbol_appears_in_main_proof(self):
        # Prevent another codepoint-only update that leaves the human proof stale.
        from pathlib import Path
        proof_source = (Path(v.__file__).parent/"proof.py").read_text(encoding="utf-8")
        self.assertIn(chr(CP), proof_source)


if __name__ == "__main__":
    unittest.main()
