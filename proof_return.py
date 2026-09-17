#!/usr/bin/env python3
"""Render the procedural U+23CE outline alone; no upstream files are required.

The temporary glyph-only host font exists in memory. This is a geometry proof,
not a full Ubuntu/Bront build and not a Windows/Qt rendering certification.
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from PIL import Image, ImageDraw, ImageFont

from vnm_font import keyboard_glyph


def make_preview(output: Path) -> None:
    width, cap, stem = 560, 700, 65
    g = keyboard_glyph(0x23CE, width, cap, stem)
    fb = FontBuilder(1000, isTTF=True)
    order = [".notdef", "space", "vnm.uni23CE"]
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap({32: "space", 0x23CE: "vnm.uni23CE"})
    fb.setupGlyf({".notdef": TTGlyphPen(None).glyph(),
                 "space": TTGlyphPen(None).glyph(), "vnm.uni23CE": g})
    fb.setupHorizontalMetrics({n: (width, g.xMin if n == "vnm.uni23CE" else 0)
                               for n in order})
    fb.setupHorizontalHeader(ascent=900, descent=-100)
    fb.setupOS2(sTypoAscender=900, sTypoDescender=-100,
                usWinAscent=900, usWinDescent=100)
    fb.setupNameTable({"familyName": "VNM Return Geometry Proof",
                       "styleName": "Regular", "psName": "VNMReturnGeometryProof"})
    fb.setupPost(isFixedPitch=1)
    fb.setupMaxp()
    data = io.BytesIO()
    fb.font.save(data)
    def face(size: int):
        return ImageFont.truetype(io.BytesIO(data.getvalue()), size,
                                 layout_engine=ImageFont.Layout.BASIC)

    image = Image.new("RGB", (1100,660), "white")
    d = ImageDraw.Draw(image)
    title = ImageFont.load_default(size=27)
    label = ImageFont.load_default(size=18)
    small = ImageFont.load_default(size=15)
    d.text((30,20), "U+23CE / hollow Return symbol", font=title, fill="black")
    d.text((30,61), "Ubuntu Sans Mono derivative vnm - builder 0.1.1", font=label, fill="black")
    d.text((30,91), "Glyph-only proof at representative metrics; not a complete Ubuntu/Bront build.",
           font=small, fill="black")
    for x0,x1,background,ink in ((30,535,"white","black"),(565,1070,"black","white")):
        d.rectangle((x0,127,x1,604), fill=background, outline="black", width=1)
        d.text((x0+20,143), "New outline / enlarged", font=label, fill=ink)
        f = face(320)
        a,b,c,e = d.textbbox((0,0), "\u23ce", font=f, anchor="ls")
        cx,cy = (x0+x1)/2, 298
        d.text((cx-(a+c)/2,cy-(b+e)/2), "\u23ce", font=f, fill=ink, anchor="ls")
        d.text((x0+20,422), "Native raster sizes (px)", font=small, fill=ink)
        for size,x in zip((16,20,24,32,48),(x0+45,x0+140,x0+235,x0+330,x0+425)):
            d.text((x,465), str(size), font=small, fill=ink)
            f = face(size)
            d.text((x,539), "\u23ce", font=f, fill=ink, anchor="ls")
        d.text((x0+20,576), "Direct FreeType rendering; no font fallback", font=small, fill=ink)
    d.text((30,624), "Two oppositely wound contours: transparent head, horizontal arm, elbow and upright tail.",
           font=small, fill="black")
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output)
    print(f"Created {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("docs/return-symbol-preview.png"))
    make_preview(parser.parse_args().output)
