#!/usr/bin/env python3
"""One-off helper (NOT stdlib: needs fontTools + brotli, e.g. the brain .venv): extract Grandstander 800
outlines for the logo letters into design/logo_glyphs.json, so build_v2.py stays stdlib-only.
Run:  python3 design/extract_glyphs.py   (needs fontTools)"""
import json
import os

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "..", "fonts")
CHARS = "MořskýsvětOceanWorldrye"
out = {"chars": {}}
for fn in ("grandstander-latin-800-normal.woff2", "grandstander-latin-ext-800-normal.woff2"):
    f = TTFont(os.path.join(FONTS, fn))
    cmap = f.getBestCmap()
    gs = f.getGlyphSet()
    out["upm"] = f["head"].unitsPerEm
    out["ascender"] = f["hhea"].ascent
    for ch in CHARS:
        if ch in out["chars"] or ord(ch) not in cmap:
            continue
        name = cmap[ord(ch)]
        pen = SVGPathPen(gs)
        gs[name].draw(pen)
        out["chars"][ch] = {"d": pen.getCommands(), "adv": f["hmtx"][name][0]}
missing = [c for c in CHARS if c not in out["chars"]]
json.dump(out, open(os.path.join(HERE, "logo_glyphs.json"), "w"), ensure_ascii=False)
print("glyphs", len(out["chars"]), "missing", missing, "upm", out["upm"])
