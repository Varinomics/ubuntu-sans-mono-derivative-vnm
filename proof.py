#!/usr/bin/env python3
"""Render direct-font proof sheets after a user-local build. No font embedding."""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, features
from fontTools.ttLib import TTFont
import vnm_font as v

HAS_RAQM = features.check_feature("raqm")
ENGINE = ImageFont.Layout.RAQM if HAS_RAQM else ImageFont.Layout.BASIC


def load(path: Path, size: int):
    return ImageFont.truetype(str(path),size,layout_engine=ENGINE)


def cap_fraction(path: Path) -> float:
    with TTFont(path) as f:
        b = v.bounds(f.getGlyphSet(), v.required(f,ord("H")))
        return (b[3]-b[1])/f["head"].unitsPerEm


def make_proofs(output: Path, bront_path: Path) -> list[str]:
    report=json.loads((output/"build-report.json").read_text(encoding="utf-8"))
    derivative=output/report["output_file"]
    upstream=output/"reference-upstream-instance.ttf"
    title=ImageFont.load_default(size=24)
    label=ImageFont.load_default(size=17)
    small=ImageFont.load_default(size=14)
    fonts=[("Original Bront - cap-height matched",bront_path),
           ("Upstream - same instance as derivative",upstream),
           ("Ubuntu Sans Mono derivative vnm",derivative)]
    target_cap=cap_fraction(derivative)
    ratio={str(p):target_cap/cap_fraction(p) for _,p in fonts}
    output_names=[]
    texts=["0 O o 1 I i l j J t G", "$ % * + - = _ __ ___ ~",
           "0x00FF  0O0O  iIl1  jJl  G6  tlt", "__init__  a_b  a__b  a * b  ~mask",
           "G Ĝ Ğ Ġ Ģ Ǧ    l ĺ ļ ľ    t ţ ť ṫ"]
    width=1580
    rows=[]
    for px in (16,22,32):
        for name,path in fonts:
            psize=max(1,round(px*ratio[str(path)]))
            face=load(path,psize)
            rows.append((f"{name}  |  {psize}px  |  comparison group {px}px",face,texts))
    total=105+sum(40+len(lines)*max(face.size*1.65,32)+20 for _,face,lines in rows)
    image=Image.new("RGB",(width,math.ceil(total)),"white")
    d=ImageDraw.Draw(image)
    d.text((30,20),"Bront / upstream / vnm - upright character proof",font=title,fill="black")
    d.text((30,55),"Direct font files; no fallback. Integer pixel sizes approximate cap-height matching.",font=small,fill="black")
    y=100.0
    for heading,face,lines in rows:
        d.line((30,y,width-30,y),fill="#cccccc")
        d.text((30,y+8),heading,font=label,fill="black")
        y+=40
        for text in lines:
            d.text((55,y),text,font=face,fill="black")
            y+=max(face.size*1.65,32)
        y+=20
    p=output/"proof-characters.png";image.save(p);output_names.append(p.name)

    code=["template <typename T>", "T update_value(T old_value, T new_value) {",
          "    const auto mask = 0x00FF;", "    auto x = (old_value * 6) - new_value;",
          "    const auto changed = (x != 0) && (x >= 1);",
          "    const auto inverse = ~mask;", "    return changed ? x : old_value;", "}",
          "// $__value  __init__  0O0O  iIl1  G6  tlt  jJl", ""]
    image=Image.new("RGB",(width,1450),"white");d=ImageDraw.Draw(image)
    d.text((30,20),"Terminal-style reading proof",font=title,fill="black")
    y=65
    for name,path in fonts:
        face=load(path,max(1,round(22*ratio[str(path)])))
        d.text((30,y),name,font=label,fill="black");y+=36
        for text in code:
            d.text((50,y),text,font=face,fill="black");y+=39
        y+=18
    p=output/"proof-reading.png";image.save(p);output_names.append(p.name)

    image=Image.new("RGB",(width,1480),"white");d=ImageDraw.Draw(image)
    d.text((30,20),"Native symbols and accents - vnm",font=title,fill="black")
    d.text((30,55),"Missing glyphs remain visibly missing; this renderer does not choose fallback fonts.",font=small,fill="black")
    y=95
    for px in (16,24,40):
        face=load(derivative,px)
        d.text((30,y),f"{px}px",font=label,fill="black");y+=33
        for text in ["⌫  ⌦  ↵  ⇥  ⇤  ↹  ⇧  ⇩  ⇪  ⎆  ⏎", "←  ↑  →  ↓", "╭──────────────╮  ┌────────┐  ╔════════╗",
                     "│ a__b * ~mask │  │ 0x00FF │  ║ G j l t║",
                     "╰──────────────╯  └────────┘  ╚════════╝",
                     "▁▂▃▄▅▆▇█  ▏▎▍▌▋▊▉█  ░▒▓█",
                     "⠁⠂⠄⠈⠐⠠⡀⢀  ⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏",
                     "\ue0a0 \ue0a1 \ue0a2  \ue0b0\ue0b1\ue0b2\ue0b3",
                     "Ĝ Ğ Ġ Ģ Ǧ  ĺ ļ ľ  ţ ť ṫ  G\u0301 l\u0301 t\u030C"]:
            d.text((55,y),text,font=face,fill="black");y+=max(35,px*1.6)
        y+=18
    d.text((30,1425),"RAQM shaping enabled: "+str(HAS_RAQM)+". Windows/Qt and terminal-cell testing is still required.",font=small,fill="black")
    p=output/"proof-symbols.png";image.save(p);output_names.append(p.name)
    (output/"proof-report.json").write_text(json.dumps({
        "images":output_names,"raqm_shaping":HAS_RAQM,
        "font_fallback":False,"cap_height_integer_size_ratios":ratio,
        "note":"These are FreeType/Pillow proofs, not Windows/Qt rendering certification"
    },indent=2)+"\n",encoding="utf-8")
    print("Rendered "+", ".join(output_names),flush=True)
    return output_names


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path,default=Path("build"))
    p.add_argument("--bront",type=Path,default=Path(".cache/vnm-font/ubuntu-mono-bront.ttf"))
    a=p.parse_args();make_proofs(a.output,a.bront)
