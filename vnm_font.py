#!/usr/bin/env python3
"""Build an upright Bront-derived variant of Ubuntu Sans Mono.

No font data is embedded here. Inputs are downloaded at pinned revisions, or
provided in a local cache. The output is a static, upright Regular prototype,
not a variable-font or italic design. See README.md for the validation limits.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import io
import json
import math
import os
from pathlib import Path
import statistics
import sys
import tempfile
from typing import Any, Iterable
import unicodedata
from urllib.parse import quote
from urllib.request import Request, urlopen

from fontTools import __version__ as FONTTOOLS_VERSION
from fontTools.misc.roundTools import otRound
from fontTools.pens.basePen import BasePen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import DecomposingRecordingPen, RecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._c_m_a_p import CmapSubtable
from fontTools.ttLib.tables._g_l_y_f import Glyph, GlyphCoordinates
from fontTools.ttLib.tables.ttProgram import Program
from fontTools.varLib.instancer import instantiateVariableFont

FAMILY = "Ubuntu Sans Mono derivative vnm"
PS_NAME = "UbuntuSansMonoDerivativeVnm-Regular"
VERSION = "0.1.0"
CORE = "$0*_- =~%GjlJt".replace(" ", "")
LETTERS = "GjlJt"
POWERLINE = (0xE0A0, 0xE0A1, 0xE0A2, 0xE0B0, 0xE0B1, 0xE0B2, 0xE0B3)
KEYBOARD = (0x232B, 0x2326, 0x21B5, 0x21E5)
UPSTREAM_REV = "c57353c1772eb8aaab9c539e3d42c971a03a5fcd"
BRONT_REV = "aef23d9a11416655a8351230edb3c2377061c077"
# Git object identifiers taken from GitHub's contents API, not ordinary SHA-1s.
INPUTS = {
    "upstream": ("canonical/Ubuntu-Sans-Mono-fonts", UPSTREAM_REV,
                 "fonts/variable/UbuntuSansMono[wght].ttf",
                 "3d8d0e73d5507976bf749a409bce276c57c51274", "upstream-variable.ttf"),
    "original": ("chrismwendt/bront", BRONT_REV, "UbuntuMono.ttf",
                 "fdd309d716629f4e5339d5e5508225ed857a3ede", "ubuntu-mono-original.ttf"),
    "bront": ("chrismwendt/bront", BRONT_REV, "UbuntuMono-Bront.ttf",
              "4731a05112ae85bd974e245c552bdf92c6ad2059", "ubuntu-mono-bront.ttf"),
    "licence": ("chrismwendt/bront", BRONT_REV, "UbuntuMono-LICENSE.txt",
                "ae78a8f94eae372cb1ca4e14b67244342fce604e", "Ubuntu-Font-Licence.txt"),
}
# 2026-09-17 00:00:00 UTC; fixed for reproducible sfnt timestamps.
DEFAULT_EPOCH = 1789603200


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def fetch_inputs(cache: Path, offline: bool = False) -> dict[str, Path]:
    cache.mkdir(parents=True, exist_ok=True)
    result: dict[str, Path] = {}
    for key, (repo, rev, path, expected, local_name) in INPUTS.items():
        target = cache / local_name
        if target.exists():
            data = target.read_bytes()
        else:
            if offline:
                raise RuntimeError(f"Offline input missing: {target}")
            url = f"https://raw.githubusercontent.com/{repo}/{rev}/{quote(path, safe='/')}"
            print(f"Downloading {local_name}", flush=True)
            request = Request(url, headers={"User-Agent": f"vnm-font-builder/{VERSION}"})
            try:
                with urlopen(request, timeout=60) as response:
                    data = response.read(8 * 1024 * 1024 + 1)
            except Exception as exc:
                raise RuntimeError(
                    f"Cannot download {local_name}: {exc}. Place the pinned original "
                    f"at {target} and rerun with --offline. See SOURCES.md."
                ) from exc
            if len(data) > 8 * 1024 * 1024:
                raise RuntimeError(f"Unexpectedly large input: {local_name}")
        actual = git_blob_sha(data)
        if actual != expected:
            raise RuntimeError(f"Input identity mismatch for {target}: expected Git blob "
                               f"{expected}, received {actual}. Input was NOT used.")
        if not target.exists():
            tmp = target.with_suffix(target.suffix + ".part")
            tmp.write_bytes(data)
            tmp.replace(target)
        result[key] = target
    return result


def cmap(font: TTFont) -> dict[int, str]:
    result = font.getBestCmap()
    if result is None:
        raise ValueError("Font has no supported Unicode character map")
    return result


def required(font: TTFont, cp: int) -> str:
    try:
        name = cmap(font)[cp]
    except KeyError as exc:
        raise ValueError(f"Required source character U+{cp:04X} is missing") from exc
    if name == ".notdef":
        raise ValueError(f"Required character U+{cp:04X} maps to .notdef")
    return name


def bounds(glyph_set: Any, name: str) -> tuple[float, float, float, float]:
    pen = BoundsPen(glyph_set)
    glyph_set[name].draw(pen)
    if pen.bounds is None:
        raise ValueError(f"Glyph {name!r} has no outline")
    return tuple(float(v) for v in pen.bounds)


def outline_signature(font: TTFont, name: str) -> tuple[Any, ...]:
    glyph_set = font.getGlyphSet()
    pen = DecomposingRecordingPen(glyph_set)
    glyph_set[name].draw(pen)
    return tuple((op, tuple(None if p is None else tuple(otRound(v) for v in p)
                           for p in points)) for op, points in pen.value)


class FlattenPen(BasePen):
    """Small scanline/proof helper; not used to construct the final outlines."""
    def __init__(self, glyph_set: Any):
        super().__init__(glyph_set)
        self.contours: list[list[tuple[float, float]]] = []
        self.current: list[tuple[float, float]] = []

    def _moveTo(self, point):
        self.current = [tuple(point)]

    def _lineTo(self, point):
        self.current.append(tuple(point))

    def _curveToOne(self, p1, p2, p3):
        p0 = self._getCurrentPoint()
        for k in range(1, 33):
            t = k / 32
            u = 1 - t
            self.current.append(tuple(u**3*p0[i] + 3*u*u*t*p1[i] +
                                      3*u*t*t*p2[i] + t**3*p3[i] for i in (0, 1)))

    def _qCurveToOne(self, p1, p2):
        p0 = self._getCurrentPoint()
        for k in range(1, 33):
            t = k / 32
            u = 1 - t
            self.current.append(tuple(u*u*p0[i] + 2*u*t*p1[i] + t*t*p2[i]
                                      for i in (0, 1)))

    def _closePath(self):
        if self.current:
            self.contours.append(self.current)
        self.current = []

    def _endPath(self):
        self._closePath()


def h_stem(font: TTFont, location: dict[str, float] | None = None) -> float:
    glyph_set = font.getGlyphSet(location=location)
    name = required(font, ord("H"))
    b = bounds(glyph_set, name)
    y = b[1] + (b[3] - b[1]) * .8
    pen = FlattenPen(glyph_set)
    glyph_set[name].draw(pen)
    intersections: list[float] = []
    for contour in pen.contours:
        for p, q in zip(contour, contour[1:] + contour[:1]):
            if (p[1] <= y < q[1]) or (q[1] <= y < p[1]):
                intersections.append(p[0] + (y-p[1])*(q[0]-p[0])/(q[1]-p[1]))
    intersections.sort()
    widths = [intersections[i+1] - intersections[i]
              for i in range(0, len(intersections)-1, 2)]
    widths = [w for w in widths if w > .1]
    if len(widths) != 2:
        raise ValueError(f"Cannot measure the two H stems: found widths {widths}")
    return float(statistics.median(widths))


def choose_weight(variable: TTFont, original: TTFont, requested: str) -> tuple[float, dict[str, float]]:
    if "fvar" not in variable:
        raise ValueError("Expected the pinned upright variable font, not a static font")
    axes = {a.axisTag: a for a in variable["fvar"].axes}
    if set(axes) != {"wght"}:
        raise ValueError(f"Unexpected variation axes: {sorted(axes)}")
    if variable["post"].italicAngle != 0:
        raise ValueError("This builder supports upright fonts only")
    axis = axes["wght"]
    old_advance = original["hmtx"].metrics[required(original, ord("H"))][0]
    native_advance = variable.getGlyphSet()[required(variable, ord("H"))].width
    target = h_stem(original) * native_advance / old_advance
    low, high = float(axis.minValue), float(axis.maxValue)
    if requested != "auto":
        value = float(requested)
        if not low <= value <= high:
            raise ValueError(f"Weight must be in [{low}, {high}]")
    else:
        a, b = h_stem(variable, {"wght": low}), h_stem(variable, {"wght": high})
        if not a <= target <= b:
            raise ValueError(f"Reference stem {target:.2f} is outside the variable font's "
                             f"range {a:.2f}..{b:.2f}; specify --weight explicitly to override")
        for _ in range(18):
            mid = (low + high) / 2
            if h_stem(variable, {"wght": mid}) < target:
                low = mid
            else:
                high = mid
        value = round((low + high) / 2, 3)
    native = h_stem(variable, {"wght": value})
    return value, {"reference_stem_in_target_units": target, "native_stem": native,
                   "native_to_reference_stem_ratio": native / target}


def static_instance(variable: TTFont, weight: float) -> TTFont:
    instance = instantiateVariableFont(variable, {"wght": weight}, inplace=False,
                                       optimize=True, updateFontNames=False)
    instance.flavor = None
    if "fvar" in instance or "gvar" in instance:
        raise ValueError("Instantiation did not produce a fully static font")
    return instance


def draw_transformed(font: TTFont, name: str, transform: tuple[float, ...]) -> Glyph:
    glyph_set = font.getGlyphSet()
    pen = TTGlyphPen(None)
    # Fully decompose donor components: their glyph IDs/names must not leak into
    # the unrelated target glyph order. TTGlyphPen keeps quadratic curves.
    recording = DecomposingRecordingPen(glyph_set)
    glyph_set[name].draw(recording)
    recording.replay(TransformPen(pen, transform))
    glyph = pen.glyph()
    glyph.recalcBounds(None)
    return glyph


def clear_program(glyph: Glyph) -> None:
    if hasattr(glyph, "program"):
        program = Program()
        program.fromBytecode([])
        glyph.program = program


def install_glyph(font: TTFont, name: str, glyph: Glyph, advance: int) -> None:
    font["glyf"][name] = glyph
    glyph.recalcBounds(font["glyf"])
    font["hmtx"].metrics[name] = (advance, int(getattr(glyph, "xMin", 0)))


def dependency_closure(font: TTFont, changed: set[str]) -> set[str]:
    result = set(changed)
    while True:
        new = {name for name in font.getGlyphOrder()
               if font["glyf"][name].isComposite() and
               any(c.glyphName in result for c in font["glyf"][name].components)}
        if new <= result:
            return result
        result.update(new)


def contour_data(glyph: Glyph, glyf: Any) -> list[tuple[list[tuple[int, int]], list[int]]]:
    coords, endpoints, flags = glyph.getCoordinates(glyf)
    result = []
    start = 0
    for end in endpoints:
        result.append(([tuple(p) for p in coords[start:end+1]],
                       [int(f) & 1 for f in flags[start:end+1]]))
        start = end + 1
    return result


def match_contour(reference, candidate) -> tuple[float, float] | None:
    rp, rf = reference
    cp, cf = candidate
    if len(rp) != len(cp) or not rp:
        return None
    for rotation in range(len(cp)):
        shifted_p = cp[rotation:] + cp[:rotation]
        shifted_f = cf[rotation:] + cf[:rotation]
        if shifted_f != rf:
            continue
        dx, dy = shifted_p[0][0]-rp[0][0], shifted_p[0][1]-rp[0][1]
        if all(abs(p[0]+dx-q[0]) < .01 and abs(p[1]+dy-q[1]) < .01
               for p, q in zip(rp, shifted_p)):
            return dx, dy
    return None


def glyph_from_contours(contours) -> Glyph:
    glyph = Glyph()
    glyph.numberOfContours = len(contours)
    coords, flags, endpoints = [], [], []
    for points, oncurve in contours:
        coords.extend(points)
        flags.extend(oncurve)
        endpoints.append(len(coords)-1)
    glyph.coordinates = GlyphCoordinates(coords)
    from array import array
    glyph.flags = array("B", flags)
    glyph.endPtsOfContours = endpoints
    glyph.program = Program()
    glyph.program.fromBytecode([])
    glyph.recalcBounds(None)
    return glyph


def replace_flattened_base(font: TTFont, name: str, old_base: Glyph,
                           new_base: Glyph, baseline: TTFont) -> bool:
    """Replace exact translated base contours in a decomposed accented glyph.

    Deliberately no fuzzy shape matching: a near match may be a different design.
    """
    if font["glyf"][name].isComposite():
        return False
    refs = contour_data(old_base, baseline["glyf"])
    candidates = contour_data(font["glyf"][name], font["glyf"])
    matches: list[int] = []
    translation = None
    for ref in refs:
        found = None
        for index, candidate in enumerate(candidates):
            if index in matches:
                continue
            offset = match_contour(ref, candidate)
            if offset is not None and (translation is None or offset == translation):
                found, translation = index, offset
                break
        if found is None:
            return False
        matches.append(found)
    if not matches or translation is None:
        return False
    dx, dy = translation
    old_top = getattr(old_base, "yMax", 0)
    new_top = getattr(new_base, "yMax", old_top)
    rise = max(0, new_top-old_top)
    kept = []
    for index, (points, flags) in enumerate(candidates):
        if index in matches:
            continue
        # Only a detached mark entirely above the previous body is moved up.
        # Side/below marks keep their original coordinates.
        mark_shift = rise if points and min(y for x, y in points) >= old_top + dy - 1 else 0
        kept.append(([(x, y+mark_shift) for x, y in points], flags))
    for points, flags in contour_data(new_base, font["glyf"]):
        kept.append(([(x+dx, y+dy) for x, y in points], flags))
    advance = font["hmtx"].metrics[name][0]
    install_glyph(font, name, glyph_from_contours(kept), advance)
    return True


def propagate_accents(font: TTFont, baseline: TTFont,
                     changed: set[str]) -> tuple[set[str], list[str], list[dict[str, Any]]]:
    cm = cmap(font)
    modified = set(changed)
    warnings: list[str] = []
    placements: list[dict[str, Any]] = []
    reachable = dependency_closure(font, changed)
    for cp, name in cm.items():
        decomposition = unicodedata.normalize("NFD", chr(cp))
        if len(decomposition) < 2 or decomposition[0] not in LETTERS:
            continue
        base = required(font, ord(decomposition[0]))
        old_base, new_base = baseline["glyf"][base], font["glyf"][base]
        if name in reachable:
            glyph = font["glyf"][name]
            # Direct base + mark composites are common. Lift detached top marks
            # when the t ascender grows, but never shift every component blindly.
            if glyph.isComposite() and any(c.glyphName == base for c in glyph.components):
                rise = max(0, getattr(new_base, "yMax", 0)-getattr(old_base, "yMax", 0))
                if rise:
                    for component in glyph.components:
                        if component.glyphName == base or not hasattr(component, "x"):
                            continue
                        pen = BoundsPen(baseline.getGlyphSet())
                        cname, matrix = component.getComponentInfo()
                        baseline.getGlyphSet()[cname].draw(TransformPen(pen, matrix))
                        if pen.bounds and pen.bounds[1] >= old_base.yMax - 1:
                            component.y += rise
                            placements.append({"glyph": name, "component": cname, "dy": rise})
                modified.add(name)
        elif replace_flattened_base(font, name, old_base, new_base, baseline):
            modified.add(name)
        else:
            warnings.append(f"U+{cp:04X} {name}: related accented form could not be "
                            "safely reconstructed; its upstream design was retained")
    modified = dependency_closure(font, modified)
    for name in modified:
        clear_program(font["glyf"][name])
    return modified, sorted(set(warnings)), placements


def adjust_mark_anchors(font: TTFont, baseline: TTFont,
                        changed: set[str]) -> list[dict[str, Any]]:
    adjustments = []
    if "GPOS" not in font:
        return adjustments
    lookup_list = getattr(font["GPOS"].table, "LookupList", None)
    if lookup_list is None:
        return adjustments
    for lookup in lookup_list.Lookup:
        for outer in lookup.SubTable:
            table = outer.ExtSubTable if lookup.LookupType == 9 else outer
            lookup_type = outer.ExtensionLookupType if lookup.LookupType == 9 else lookup.LookupType
            if lookup_type != 4 or getattr(table, "Format", None) != 1:
                continue
            for name, record in zip(table.BaseCoverage.glyphs, table.BaseArray.BaseRecord):
                if name not in changed:
                    continue
                old = bounds(baseline.getGlyphSet(), name)
                new = bounds(font.getGlyphSet(), name)
                rise = max(0, new[3]-old[3])
                for index, anchor in enumerate(record.BaseAnchor):
                    if anchor is None:
                        continue
                    converted = anchor.Format == 2
                    if converted:
                        # The donor's point numbering is unrelated to upstream.
                        anchor.Format = 1
                        if hasattr(anchor, "AnchorPoint"):
                            del anchor.AnchorPoint
                    delta_y = rise if anchor.YCoordinate >= old[3]-1 else 0
                    if delta_y:
                        anchor.YCoordinate += otRound(delta_y)
                    if converted or delta_y:
                        adjustments.append({"glyph": name, "anchor": index,
                                            "dy": delta_y, "point_anchor_promoted": converted})
    return adjustments


def polygon(pen: TTGlyphPen, points: list[tuple[float, float]], clockwise: bool = True) -> None:
    area2 = sum(p[0]*q[1]-q[0]*p[1] for p, q in zip(points, points[1:]+points[:1]))
    if (area2 < 0) != clockwise:
        points = list(reversed(points))
    pen.moveTo(points[0])
    for p in points[1:]:
        pen.lineTo(p)
    pen.closePath()


def keyboard_glyph(cp: int, width: float, cap: float, stem: float) -> Glyph:
    """Original geometric key/arrow outlines, with no fallback font dependency."""
    pen = TTGlyphPen(None)
    s = max(20.0, min(stem * .72, width * .095))
    left, right = width*.07, width*.93
    bottom, top = cap*.22, cap*.78
    cy = (bottom+top)/2
    if cp in (0x232B, 0x2326):
        neck = left+width*.23
        outer = [(left,cy), (neck,top), (right,top), (right,bottom), (neck,bottom)]
        inner = [(left+s*1.5,cy), (neck+s*.35,top-s), (right-s,top-s),
                 (right-s,bottom+s), (neck+s*.35,bottom+s)]
        cx = (neck+right)/2
        r = min((right-neck)*.22, (top-bottom)*.25)
        d = s*.47
        cross = [(cx-r-d,cy+r-d),(cx-r+d,cy+r+d),(cx,cy+2*d),
                 (cx+r-d,cy+r+d),(cx+r+d,cy+r-d),(cx+2*d,cy),
                 (cx+r+d,cy-r+d),(cx+r-d,cy-r-d),(cx,cy-2*d),
                 (cx-r+d,cy-r-d),(cx-r-d,cy-r+d),(cx-2*d,cy)]
        if cp == 0x2326:
            outer = [(width-x,y) for x,y in outer]
            inner = [(width-x,y) for x,y in inner]
            cross = [(width-x,y) for x,y in cross]
        polygon(pen, outer)
        polygon(pen, inner, clockwise=False)
        polygon(pen, cross)
    elif cp == 0x21B5:
        y = cap*.35
        tail = width*.85
        tip = width*.1
        neck = width*.35
        rise = cap*.2
        points = [(tip,y), (neck,y+rise), (neck,y+s/2),
                  (tail-s/2,y+s/2), (tail-s/2,cap*.9), (tail+s/2,cap*.9),
                  (tail+s/2,y-s/2), (neck,y-s/2), (neck,y-rise)]
        polygon(pen, points)
    elif cp == 0x21E5:
        y = cap*.5
        neck, tip, bar = width*.51, width*.77, width*.88
        rise = cap*.21
        polygon(pen, [(left,y-s/2),(neck,y-s/2),(neck,y-rise),(tip,y),
                      (neck,y+rise),(neck,y+s/2),(left,y+s/2)])
        polygon(pen, [(bar-s/2,cap*.2),(bar-s/2,cap*.8),
                      (bar+s/2,cap*.8),(bar+s/2,cap*.2)])
    else:
        raise ValueError(f"Unsupported keyboard glyph U+{cp:04X}")
    result = pen.glyph()
    result.recalcBounds(None)
    return result


def add_mapping(font: TTFont, cp: int, name: str, glyph: Glyph, width: int) -> None:
    if cp in cmap(font):
        raise ValueError(f"Refusing to overwrite existing U+{cp:04X}")
    order = font.getGlyphOrder()
    if name in order:
        raise ValueError(f"Glyph name collision: {name}")
    font.setGlyphOrder(order + [name])
    install_glyph(font, name, glyph, width)
    updated = False
    for table in font["cmap"].tables:
        if table.isUnicode() and table.format in (4, 12):
            if cp <= 0xFFFF or table.format == 12:
                table.cmap[cp] = name
                updated = True
    if not updated:
        table = CmapSubtable.newSubtable(12)
        table.platformID, table.platEncID, table.language = 3, 10, 0
        table.cmap = dict(cmap(font))
        table.cmap[cp] = name
        font["cmap"].tables.append(table)
    font["maxp"].numGlyphs = len(font.getGlyphOrder())


def rename(font: TTFont, epoch: int) -> None:
    names = font["name"]
    names_to_replace = {1,2,3,4,5,6,16,17,18,21,22,25}
    names.names = [record for record in names.names if record.nameID not in names_to_replace]
    values = {
        1: FAMILY, 2: "Regular", 3: f"1.101;VNM;{PS_NAME}",
        4: f"{FAMILY} Regular", 5: f"Version 1.101; vnm {VERSION}; upstream 1.100",
        6: PS_NAME, 16: FAMILY, 17: "Regular",
    }
    for key, value in values.items():
        names.setName(value, key, 3, 1, 0x409)
        names.setName(value, key, 0, 4, 0)
        names.setName(value, key, 1, 0, 0)
    for record in list(names.names):
        if record.nameID == 0:
            text = record.toUnicode()
            note = " Bront modifications by Chris Wendt; vnm derivative 2026."
            if note not in text:
                names.setName(text+note, 0, record.platformID, record.platEncID, record.langID)
    font["OS/2"].achVendID = "VNM "
    font["OS/2"].usWeightClass = 400  # derivative family's named Regular style
    font["OS/2"].fsSelection = (font["OS/2"].fsSelection & ~((1<<0)|(1<<5)|(1<<9))) | (1<<6)
    font["head"].macStyle &= ~3
    font["head"].fontRevision = 1.101
    font["head"].created = font["head"].modified = epoch + 2082844800
    font.recalcTimestamp = False
    font["post"].italicAngle = 0
    font["post"].isFixedPitch = 1
    for tag in ("DSIG", "FFTM", "STAT"):
        if tag in font:
            del font[tag]
    font["OS/2"].recalcUnicodeRanges(font)


def build_variant(upstream: TTFont, original: TTFont, bront: TTFont,
                  keyboard: bool = True, powerline: bool = True,
                  epoch: int = DEFAULT_EPOCH) -> tuple[TTFont, dict[str, Any]]:
    if "fvar" in upstream:
        raise ValueError("Instantiate the upstream variable font before applying the patch")
    if any("glyf" not in f for f in (upstream, original, bront)):
        raise ValueError("TrueType outlines are required")
    font = copy.deepcopy(upstream)
    font.flavor = None
    baseline = copy.deepcopy(upstream)
    if original["head"].unitsPerEm != bront["head"].unitsPerEm:
        raise ValueError("Original/Bront units-per-em differ; donor scaling would be unsafe")
    anticipated = {required(baseline,ord(c)) for c in CORE}
    for name in dependency_closure(baseline,anticipated):
        g=baseline["glyf"][name]
        if g.isComposite() and any(not hasattr(c,"x") for c in g.components):
            raise ValueError(f"Point-attached dependent composite {name}: "
                             "requires conversion to XY placement before patching")
    old_gs, new_gs = original.getGlyphSet(), baseline.getGlyphSet()
    old_h = bounds(old_gs, required(original, ord("H")))
    new_h = bounds(new_gs, required(baseline, ord("H")))
    advance = baseline["hmtx"].metrics[required(baseline, ord("H"))][0]
    old_advance = original["hmtx"].metrics[required(original, ord("H"))][0]
    sx = advance / old_advance
    sy = (new_h[3]-new_h[1]) / (old_h[3]-old_h[1])
    baseline_y = new_h[1]-old_h[1]*sy
    if not .25 < sx < 4 or not .25 < sy < 4:
        raise ValueError("Unreasonable source-to-target scale")
    native_plus = bounds(new_gs, required(baseline, ord("+")))
    bront_hyphen = bounds(bront.getGlyphSet(), required(bront, ord("-")))
    operator_y = (native_plus[1]+native_plus[3])/2 - (bront_hyphen[1]+bront_hyphen[3])*sy/2
    core_names: set[str] = set()
    operations = []
    for char in CORE:
        cp = ord(char)
        name, donor = required(font, cp), required(bront, cp)
        dy = operator_y if char in "*-= " else baseline_y
        # Preserve the upstream underscore's placement below the baseline;
        # change its shape/width, not the whole family's underline position.
        if char == "_":
            native_box = bounds(new_gs, name)
            donor_box = bounds(bront.getGlyphSet(), donor)
            dy = (native_box[1]+native_box[3])/2 - (donor_box[1]+donor_box[3])*sy/2
        glyph = draw_transformed(bront, donor, (sx,0,0,sy,0,dy))
        original_advance = font["hmtx"].metrics[name][0]
        install_glyph(font, name, glyph, original_advance)
        core_names.add(name)
        operations.append({"codepoint": f"U+{cp:04X}", "character": char,
                           "glyph": name, "transform": [sx,0,0,sy,0,dy]})
    modified, warnings, placements = propagate_accents(font, baseline, core_names)
    anchors = adjust_mark_anchors(font, baseline, core_names)
    # Do not silently claim alternate/oldstyle numeral designs were ported.
    alternate_zero = sorted(n for n in font.getGlyphOrder()
                            if n.startswith("zero.") and n not in modified)
    if alternate_zero:
        warnings.append("Alternate zero designs retained from upstream: " + ", ".join(alternate_zero))
    added = []
    if keyboard:
        for cp in KEYBOARD:
            if cp in cmap(font):
                continue
            name = f"vnm.uni{cp:04X}"
            glyph = keyboard_glyph(cp, advance, new_h[3], h_stem(baseline))
            add_mapping(font, cp, name, glyph, advance)
            added.append({"codepoint": f"U+{cp:04X}", "glyph": name, "source": "vnm geometry"})
    if powerline:
        for cp in POWERLINE:
            if cp in cmap(font):
                continue
            donor = required(bront, cp)
            # Symbols use the same body scaling as the text. Font-cell seams
            # still need inspection at the terminal's chosen line spacing.
            glyph = draw_transformed(bront, donor, (sx,0,0,sy,0,baseline_y))
            name = f"vnm.uni{cp:04X}"
            add_mapping(font, cp, name, glyph, advance)
            added.append({"codepoint": f"U+{cp:04X}", "glyph": name, "source": "Bront"})
    rename(font, epoch)
    report = {
        "builder_version": VERSION, "fonttools_version": FONTTOOLS_VERSION,
        "family": FAMILY, "style": "Regular", "scope": "upright static prototype",
        "scale": {"x": sx, "y": sy, "baseline_y": baseline_y},
        "operations": operations, "modified_or_dependent_glyphs": sorted(modified),
        "added_glyphs": added, "accent_component_adjustments": placements,
        "mark_anchor_adjustments": anchors, "warnings": warnings,
        "hinting": "Upstream instructions preserved except on changed glyphs and their dependent composites; modified outlines are unhinted",
        "programming_ligatures_added": False,
    }
    return font, report


def validate(baseline: TTFont, result: TTFont, report: dict[str, Any],
             require_full_coverage: bool = True, keyboard: bool = True,
             powerline: bool = True) -> dict[str, Any]:
    old_map, new_map = cmap(baseline), cmap(result)
    missing = sorted(set(old_map)-set(new_map))
    remapped = [cp for cp, name in old_map.items() if new_map.get(cp) != name]
    if missing or remapped:
        raise AssertionError(f"Upstream mapping regression: missing={missing}, remapped={remapped}")
    original_order = baseline.getGlyphOrder()
    if result.getGlyphOrder()[:len(original_order)] != original_order:
        raise AssertionError("Original glyph IDs were reordered")
    if any(result["hmtx"].metrics[n][0] != baseline["hmtx"].metrics[n][0] for n in original_order):
        raise AssertionError("An existing advance width changed")
    allowed = set(report["modified_or_dependent_glyphs"])
    unexpectedly_changed = [n for n in original_order if n not in allowed and
                            outline_signature(baseline,n) != outline_signature(result,n)]
    if unexpectedly_changed:
        raise AssertionError(f"Unexpected outline changes: {unexpectedly_changed[:20]}")
    i_name = required(result, ord("i"))
    if outline_signature(baseline,i_name) != outline_signature(result,i_name):
        raise AssertionError("Lowercase i was changed")
    if result["name"].getDebugName(1) != FAMILY or result["name"].getDebugName(6) != PS_NAME:
        raise AssertionError("Derivative naming failed")
    if "fvar" in result or "gvar" in result:
        raise AssertionError("Unexpected variation tables in static output")
    full_blocks = {"box_drawing": (0x2500,0x2580), "block_elements": (0x2580,0x25A0),
                   "braille": (0x2800,0x2900)}
    block_counts = {}
    for key,(a,b) in full_blocks.items():
        count = sum(cp in new_map for cp in range(a,b))
        block_counts[key] = {"mapped": count, "expected": b-a}
        if require_full_coverage and count != b-a:
            raise AssertionError(f"{key}: expected full upstream coverage, found {count}/{b-a}")
    required_extra = list(KEYBOARD if keyboard else ()) + list(POWERLINE if powerline else ())
    extra_checks = {}
    for cp in required_extra:
        n = required(result, cp)
        b = bounds(result.getGlyphSet(),n)
        if b[2] <= b[0] or b[3] <= b[1]:
            raise AssertionError(f"Empty added symbol U+{cp:04X}")
        extra_checks[f"U+{cp:04X}"] = True
    for tag in ("GSUB",):
        if (tag in baseline) != (tag in result):
            raise AssertionError(f"{tag} was added or removed unexpectedly")
        if tag in baseline and baseline[tag].compile(baseline) != result[tag].compile(result):
            raise AssertionError(f"{tag} changed unexpectedly")
    for attribute in ("ascent", "descent", "lineGap"):
        if getattr(baseline["hhea"],attribute) != getattr(result["hhea"],attribute):
            raise AssertionError(f"hhea {attribute} changed")
    for attribute in ("sTypoAscender", "sTypoDescender", "sTypoLineGap", "usWinAscent", "usWinDescent"):
        if getattr(baseline["OS/2"],attribute) != getattr(result["OS/2"],attribute):
            raise AssertionError(f"OS/2 {attribute} changed")
    return {
        "status": "PASS", "upstream_mapped_codepoints": len(old_map),
        "result_mapped_codepoints": len(new_map), "missing_upstream_codepoints": [],
        "preserved_original_glyph_ids": len(original_order),
        "preserved_original_advances": len(original_order),
        "unchanged_unrelated_outlines": True, "unchanged_lowercase_i": True,
        "unchanged_line_metrics": True, "unchanged_GSUB": True,
        "blocks": block_counts, "extra_symbols": extra_checks,
        "scope_note": "Structural checks, not Windows/Qt rendering certification",
    }


def save_atomic(font: TTFont, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(suffix=".ttf", dir=path.parent)
    os.close(fd)
    temp = Path(temp_name)
    try:
        font.save(temp, reorderTables=True)
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)


def run(args: argparse.Namespace) -> dict[str, Any]:
    print("Building an upright Regular prototype; production hinting and visual acceptance are not certified.", flush=True)
    inputs = fetch_inputs(Path(args.cache), args.offline)
    variable = TTFont(io.BytesIO(inputs["upstream"].read_bytes()), recalcTimestamp=False)
    original = TTFont(io.BytesIO(inputs["original"].read_bytes()), recalcTimestamp=False)
    bront = TTFont(io.BytesIO(inputs["bront"].read_bytes()), recalcTimestamp=False)
    weight, measurement = choose_weight(variable, original, args.weight)
    print(f"Upstream source weight: {weight:g}", flush=True)
    baseline = static_instance(variable, weight)
    epoch = int(os.environ.get("SOURCE_DATE_EPOCH", DEFAULT_EPOCH))
    font, report = build_variant(baseline, original, bront,
                                 not args.no_keyboard, not args.no_powerline, epoch)
    measurement["instanced_native_stem"] = h_stem(baseline)
    report.update({"upstream_release": "v1.100", "upstream_revision": UPSTREAM_REV,
                   "bront_revision": BRONT_REV, "upstream_source_weight": weight,
                   "weight_selection": args.weight, "stroke_measurement": measurement,
                   "input_sha256": {key: hashlib.sha256(path.read_bytes()).hexdigest()
                                    for key,path in inputs.items()}})
    output = Path(args.output)
    # Keep an invalid or partially written candidate out of the public output path.
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="vnm-validate-", dir=output) as td:
        candidate = Path(td)/"candidate.ttf"
        baseline_path = Path(td)/"baseline.ttf"
        save_atomic(font, candidate)
        save_atomic(baseline, baseline_path)
        reloaded = TTFont(io.BytesIO(candidate.read_bytes()), recalcTimestamp=False)
        normalized_baseline = TTFont(io.BytesIO(baseline_path.read_bytes()), recalcTimestamp=False)
        report["validation"] = validate(normalized_baseline, reloaded, report,
                                        keyboard=not args.no_keyboard,
                                        powerline=not args.no_powerline)
        data = candidate.read_bytes()
        target = output/f"{PS_NAME}.ttf"
        fd, temp_name = tempfile.mkstemp(prefix=".vnm-", dir=output)
        os.close(fd)
        tmp = Path(temp_name)
        try:
            tmp.write_bytes(data)
            tmp.replace(target)
        finally:
            tmp.unlink(missing_ok=True)
        # User-local reference instance for matched proofs; not an installation font.
        (output/"reference-upstream-instance.ttf").write_bytes(baseline_path.read_bytes())
    (output/"Ubuntu-Font-Licence.txt").write_bytes(inputs["licence"].read_bytes())
    (output/"NOTICE.txt").write_text(
        "Ubuntu Sans Mono derivative vnm — upright Regular prototype\n"
        "Based on Canonical's Ubuntu Sans Mono v1.100 and Chris Wendt's Ubuntu Mono - Bront.\n"
        "Font output is governed by the accompanying Ubuntu Font Licence 1.0.\n"
        "No endorsement by Canonical or Chris Wendt is implied.\n"
        "Modified outlines have not received fresh production TrueType hinting.\n",
        encoding="utf-8")
    report["output_file"] = target.name
    report["output_sha256"] = hashlib.sha256(data).hexdigest()
    (output/"build-report.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(f"Created {target}\nValidation: PASS", flush=True)
    for warning in report["warnings"]:
        print("Review: " + warning, flush=True)
    if args.proof:
        from proof import make_proofs
        make_proofs(output, inputs["bront"])
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", default=".cache/vnm-font")
    parser.add_argument("--output", default="build")
    parser.add_argument("--weight", default="auto", help="auto matches reference H stems; or a native upstream weight, e.g. 473")
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--no-keyboard", action="store_true")
    parser.add_argument("--no-powerline", action="store_true")
    parser.add_argument("--proof", action="store_true", help="render PNG proof sheets; requires Pillow")
    args = parser.parse_args()
    try:
        run(args)
    except (Exception, KeyboardInterrupt) as exc:
        print(f"Build failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
