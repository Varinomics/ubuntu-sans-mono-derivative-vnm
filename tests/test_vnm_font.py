"""Structural tests with generated synthetic fonts, NOT actual-font acceptance tests."""
from __future__ import annotations
import copy
import argparse
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from fontTools.fontBuilder import FontBuilder
from fontTools.designspaceLib import DesignSpaceDocument, AxisDescriptor, SourceDescriptor
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont
from fontTools.varLib import build

import vnm_font as v


def box(x0,y0,x1,y1):
    p = TTGlyphPen(None)
    v.polygon(p, [(x0,y0),(x0,y1),(x1,y1),(x1,y0)])
    return p.glyph()


def H(stem, width):
    p = TTGlyphPen(None)
    left, right = 50, width-50
    s = stem
    v.polygon(p, [(left,0),(left,700),(left+s,700),(left+s,380),
                  (right-s,380),(right-s,700),(right,700),(right,0),
                  (right-s,0),(right-s,320),(left+s,320),(left+s,0)])
    return p.glyph()


def fixture(width=600, stem=40, donor=False, extras=True):
    cm = {cp: chr(cp) if chr(cp).isalnum() else f"u{cp:04X}" for cp in range(32,127)}
    cm.update({0x0301: "acutecomb", 0x030C: "caroncomb", 0x01F4:"Gacute",
               0x013A:"lacute", 0x0165:"tcaron"})
    if extras:
        for a,b in [(0x2500,0x25A0),(0x2800,0x2900)]:
            cm.update({cp:f"u{cp:04X}" for cp in range(a,b)})
    if donor:
        cm.update({cp:f"u{cp:04X}" for cp in v.POWERLINE})
    glyphs = {name:box(40,0,width-40,500) for name in cm.values()}
    glyphs[".notdef"] = box(50,0,width-50,700)
    glyphs[cm[32]] = TTGlyphPen(None).glyph()
    glyphs["H"] = H(stem,width)
    glyphs["i"] = box(width*.4,0,width*.4+stem,500)
    glyphs["l"] = box(width*.4,0,width*.4+stem,700)
    glyphs["t"] = box(width*.4,0,width*.4+stem,560)
    glyphs[cm[ord("+")]] = box(70,280,width-70,380)
    glyphs[cm[ord("-")]] = box(100,300,width-100,350)
    glyphs[cm[ord("_")]] = box(100,-100,width-100,-50)
    glyphs["acutecomb"] = box(0,0,50,60)
    glyphs["caroncomb"] = box(0,0,70,60)
    if donor:
        for char in v.CORE:
            # Different fixture design, to verify dispatch/scaling, not aesthetics.
            glyphs[cm[ord(char)]] = box(65,0,width-90,630)
        glyphs["t"] = box(150,0,150+stem,700)
        glyphs["l"] = box(155,0,155+stem,700)
        glyphs[cm[ord("-")]] = box(90,300,width-90,340)
        glyphs[cm[ord("_")]] = box(90,-110,width-90,-70)
        glyphs[cm[ord("=")]] = box(90,280,width-90,360)
        glyphs[cm[ord("*")]] = box(110,220,width-110,420)
    p = TTGlyphPen(glyphs)
    p.addComponent("G",(1,0,0,1,0,0))
    p.addComponent("acutecomb",(1,0,0,1,200,720))
    glyphs["Gacute"] = p.glyph()
    p = TTGlyphPen(glyphs)
    p.addComponent("t",(1,0,0,1,0,0))
    p.addComponent("caroncomb",(1,0,0,1,200,580))
    glyphs["tcaron"] = p.glyph()
    # A decomposed accent, deliberately not a composite.
    tmp = copy.deepcopy(glyphs["l"])
    contours = v.contour_data(tmp,None) + [([(200,720),(200,780),(250,780),(250,720)],[1]*4)]
    glyphs["lacute"] = v.glyph_from_contours(contours)
    glyphs["fi"] = box(50,0,width-50,600)
    glyphs["zero.osf"] = box(50,0,width-50,400)
    order = [".notdef"] + sorted(name for name in glyphs if name != ".notdef")
    fb = FontBuilder(1000,isTTF=True)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap(cm)
    fb.setupGlyf(glyphs)
    metrics = {n:(width, getattr(glyphs[n],"xMin",0)) for n in order}
    metrics["acutecomb"] = (0,0)
    metrics["caroncomb"] = (0,0)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=1000,descent=-300,lineGap=0)
    fb.setupNameTable({"familyName":"Synthetic Fixture", "styleName":"Regular",
                       "uniqueFontIdentifier":"fixture", "fullName":"Synthetic Fixture Regular",
                       "psName":"SyntheticFixture-Regular", "version":"Version 1.0",
                       "copyright":"Synthetic test data"})
    fb.setupOS2(sTypoAscender=1000,sTypoDescender=-300,sTypoLineGap=0,
                usWinAscent=1100,usWinDescent=300,usWeightClass=400)
    fb.setupPost(isFixedPitch=1)
    fb.setupMaxp()
    font=fb.font
    addOpenTypeFeaturesFromString(font, """
        languagesystem DFLT dflt;
        markClass acutecomb <anchor 0 0> @TOP;
        feature mark {
          pos base t <anchor 250 580> mark @TOP;
          pos base G <anchor 250 720> mark @TOP;
        } mark;
        feature liga { sub f i by fi; } liga;
    """)
    return font


class DerivativeTests(unittest.TestCase):
    def setUp(self):
        self.original = fixture(width=500,stem=60)
        self.bront = fixture(width=500,stem=60,donor=True)
        self.upstream = fixture(width=600,stem=72)

    def test_core_is_thirteen_and_excludes_i(self):
        self.assertEqual(len(v.CORE),13)
        self.assertEqual(len(set(v.CORE)),13)
        self.assertNotIn("i",v.CORE)

    def test_weight_stem_measurement(self):
        self.assertEqual(v.h_stem(self.original),60)
        self.assertEqual(v.h_stem(self.upstream),72)

    def test_static_roundtrip_and_structural_validation(self):
        result,report=v.build_variant(self.upstream,self.original,self.bront)
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)
            v.save_atomic(result,p/"result.ttf")
            v.save_atomic(self.upstream,p/"baseline.ttf")
            reread=TTFont(io.BytesIO((p/"result.ttf").read_bytes()))
            baseline=TTFont(io.BytesIO((p/"baseline.ttf").read_bytes()))
            checked=v.validate(baseline,reread,report)
        self.assertEqual(checked["status"],"PASS")
        self.assertEqual(checked["result_mapped_codepoints"]-checked["upstream_mapped_codepoints"],11)
        self.assertEqual(len(report["operations"]),13)

    def test_lowercase_i_outline_and_instructions_survive(self):
        p=v.Program(); p.fromBytecode([0x00])
        self.upstream["glyf"]["i"].program=p
        before=v.outline_signature(self.upstream,"i")
        result,_=v.build_variant(self.upstream,self.original,self.bront)
        self.assertEqual(v.outline_signature(result,"i"),before)
        self.assertEqual(result["glyf"]["i"].program.getBytecode(),b"\0")

    def test_all_advance_widths_and_ids_are_preserved(self):
        result,_=v.build_variant(self.upstream,self.original,self.bront)
        old=self.upstream.getGlyphOrder()
        self.assertEqual(result.getGlyphOrder()[:len(old)],old)
        for name in old:
            self.assertEqual(result["hmtx"].metrics[name][0], self.upstream["hmtx"].metrics[name][0])

    def test_direct_composite_tracks_base_and_top_mark_moves(self):
        result,report=v.build_variant(self.upstream,self.original,self.bront)
        self.assertIn("Gacute",report["modified_or_dependent_glyphs"])
        self.assertNotEqual(v.outline_signature(result,"Gacute"),v.outline_signature(self.upstream,"Gacute"))
        self.assertEqual(result["glyf"]["tcaron"].components[1].y,720)
        self.assertTrue(report["accent_component_adjustments"])

    def test_flattened_accent_replacement(self):
        result,report=v.build_variant(self.upstream,self.original,self.bront)
        self.assertIn("lacute",report["modified_or_dependent_glyphs"])
        self.assertNotEqual(v.outline_signature(result,"lacute"),v.outline_signature(self.upstream,"lacute"))

    def test_anchor_top_moves_and_invalid_point_index_removed(self):
        table=self.upstream["GPOS"].table.LookupList.Lookup[0].SubTable[0]
        index=table.BaseCoverage.glyphs.index("t")
        anchor=table.BaseArray.BaseRecord[index].BaseAnchor[0]
        anchor.Format=2; anchor.AnchorPoint=999
        result,report=v.build_variant(self.upstream,self.original,self.bront)
        new=result["GPOS"].table.LookupList.Lookup[0].SubTable[0].BaseArray.BaseRecord[index].BaseAnchor[0]
        self.assertEqual(new.Format,1)
        self.assertFalse(hasattr(new,"AnchorPoint"))
        self.assertEqual(new.YCoordinate,720)
        self.assertTrue(report["mark_anchor_adjustments"])

    def test_hyphen_underscore_width_equal_operators_centered(self):
        result,_=v.build_variant(self.upstream,self.original,self.bront)
        gs=result.getGlyphSet()
        boxes={c:v.bounds(gs,v.required(result,ord(c))) for c in "-_+*= " if c!=" "}
        self.assertEqual(boxes["-"][2]-boxes["-"][0],boxes["_"][2]-boxes["_"][0])
        for c in "-*=":
            self.assertEqual((boxes[c][1]+boxes[c][3])/2,(boxes["+"][1]+boxes["+"][3])/2)

    def test_existing_keyboard_glyph_not_overwritten(self):
        v.add_mapping(self.upstream,0x232B,"existingBackspace",box(11,22,333,444),600)
        result,report=v.build_variant(self.upstream,self.original,self.bront)
        self.assertEqual(v.required(result,0x232B),"existingBackspace")
        self.assertEqual(v.outline_signature(result,"existingBackspace"),
                         v.outline_signature(self.upstream,"existingBackspace"))
        self.assertEqual(len(report["added_glyphs"]),10)

    def test_optional_extras_disabled(self):
        result,report=v.build_variant(self.upstream,self.original,self.bront,keyboard=False,powerline=False)
        self.assertEqual(set(v.cmap(result)),set(v.cmap(self.upstream)))
        self.assertEqual(report["added_glyphs"],[])
        v.validate(self.upstream,result,report,keyboard=False,powerline=False)

    def test_every_keyboard_glyph_is_nonempty_and_within_cell(self):
        for cp in v.KEYBOARD:
            glyph=v.keyboard_glyph(cp,560,700,65)
            self.assertGreater(glyph.numberOfContours,0)
            self.assertGreaterEqual(glyph.xMin,0)
            self.assertLessEqual(glyph.xMax,560)
            self.assertGreaterEqual(glyph.yMin,0)
            self.assertLessEqual(glyph.yMax,700)

    def test_derivative_name_all_platforms(self):
        result,_=v.build_variant(self.upstream,self.original,self.bront)
        self.assertEqual(len(v.FAMILY),31)
        for n in result["name"].names:
            if n.nameID in (1,16): self.assertEqual(n.toUnicode(),v.FAMILY)
            if n.nameID==6: self.assertEqual(n.toUnicode(),v.PS_NAME)
        self.assertEqual(result["OS/2"].usWeightClass,400)
        self.assertEqual(result["post"].italicAngle,0)

    def test_save_is_reproducible(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)
            a,_=v.build_variant(self.upstream,self.original,self.bront)
            b,_=v.build_variant(self.upstream,self.original,self.bront)
            v.save_atomic(a,p/"a.ttf");v.save_atomic(b,p/"b.ttf")
            self.assertEqual((p/"a.ttf").read_bytes(),(p/"b.ttf").read_bytes())

    def test_unrelated_outline_mutation_is_detected(self):
        result,report=v.build_variant(self.upstream,self.original,self.bront)
        v.install_glyph(result,"A",box(2,3,400,500),600)
        with self.assertRaisesRegex(AssertionError,"Unexpected outline changes"):
            v.validate(self.upstream,result,report)

    def test_missing_coverage_is_detected(self):
        result,report=v.build_variant(self.upstream,self.original,self.bront)
        for table in result["cmap"].tables:
            if hasattr(table,"cmap"): table.cmap.pop(0x2801,None)
        with self.assertRaisesRegex(AssertionError,"mapping regression"):
            v.validate(self.upstream,result,report)

    def test_missing_source_character_is_rejected(self):
        for table in self.bront["cmap"].tables:
            if hasattr(table,"cmap"): table.cmap.pop(ord("$"),None)
        with self.assertRaisesRegex(ValueError,"U\\+0024"):
            v.build_variant(self.upstream,self.original,self.bront)

    def test_corrupt_cached_input_is_not_used(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)
            (p/v.INPUTS["upstream"][4]).write_bytes(b"not a font")
            with self.assertRaisesRegex(RuntimeError,"identity mismatch"):
                v.fetch_inputs(p,offline=True)

    def test_offline_missing_input_is_explained(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(RuntimeError,"Offline input missing"):
                v.fetch_inputs(Path(td),offline=True)

    def test_git_blob_hash_convention(self):
        self.assertEqual(v.git_blob_sha(b""),"e69de29bb2d1d6434b8b29ae775ad8c2e48c5391")

    def test_variation_weight_auto_and_real_instancing_on_synthetic_masters(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)
            doc=DesignSpaceDocument()
            axis=AxisDescriptor();axis.name="Weight";axis.tag="wght"
            axis.minimum=400;axis.default=400;axis.maximum=700
            doc.addAxis(axis)
            for value,stem in [(400,40),(700,100)]:
                f=fixture(width=600,stem=stem)
                f["OS/2"].usWeightClass=value
                path=p/f"master-{value}.ttf"; f.save(path)
                s=SourceDescriptor();s.path=str(path);s.name=str(value)
                s.location={"Weight":value};s.familyName="Synthetic Fixture";s.styleName=str(value)
                s.font=f
                if value==400: s.copyInfo=True;s.copyLib=True;s.copyFeatures=True
                doc.addSource(s)
            doc.write(p/"fixture.designspace")
            variable,_,_=build(doc)
            value,measurement=v.choose_weight(variable,self.original,"auto")
            self.assertAlmostEqual(value,560,delta=.1)
            self.assertAlmostEqual(measurement["native_to_reference_stem_ratio"],1,delta=.001)
            instance=v.static_instance(variable,value)
            self.assertNotIn("fvar",instance)
            result,report=v.build_variant(instance,self.original,self.bront)
            v.save_atomic(instance,p/"baseline.ttf")
            v.save_atomic(result,p/"result.ttf")
            checked=v.validate(TTFont(io.BytesIO((p/"baseline.ttf").read_bytes())),TTFont(io.BytesIO((p/"result.ttf").read_bytes())),report)
            self.assertEqual(checked["status"],"PASS")

    def test_complete_offline_driver_and_proofs_with_synthetic_inputs(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td); cache=p/"cache";cache.mkdir()
            doc=DesignSpaceDocument()
            axis=AxisDescriptor();axis.name="Weight";axis.tag="wght"
            axis.minimum=400;axis.default=400;axis.maximum=700;doc.addAxis(axis)
            for value,stem in [(400,40),(700,100)]:
                f=fixture(width=600,stem=stem);f["OS/2"].usWeightClass=value
                source=SourceDescriptor();source.font=f;source.name=str(value)
                source.location={"Weight":value};source.familyName="Synthetic Fixture";source.styleName=str(value)
                if value==400:source.copyInfo=True
                doc.addSource(source)
            variable,_,_=build(doc)
            variable.save(cache/"variable.ttf")
            self.original.save(cache/"original.ttf");self.bront.save(cache/"bront.ttf")
            (cache/"licence.txt").write_text("SYNTHETIC TEST LICENCE - NOT FONT DISTRIBUTION DATA")
            mapped={}
            for key,name in [("upstream","variable.ttf"),("original","original.ttf"),
                             ("bront","bront.ttf"),("licence","licence.txt")]:
                mapped[key]=("test/fixture","test",name,v.git_blob_sha((cache/name).read_bytes()),name)
            args=argparse.Namespace(cache=str(cache),offline=True,weight="auto",
                                    output=str(p/"out"),no_keyboard=False,no_powerline=False,proof=True)
            with patch.dict(v.INPUTS,mapped,clear=True):
                report=v.run(args)
            self.assertEqual(report["validation"]["status"],"PASS")
            from PIL import Image
            for name in ("proof-characters.png","proof-reading.png","proof-symbols.png"):
                with Image.open(p/"out"/name) as im:
                    self.assertGreater(im.width,1000)
                    self.assertGreater(im.height,1000)


if __name__=="__main__":
    unittest.main()
