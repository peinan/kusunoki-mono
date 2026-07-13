"""Apply a per-glyph icon downscale plan (from plan_icon_scale.py) to a font.
Each listed glyph is scaled about its ink centre; the advance width is kept so
the smaller icon simply sits centred in the same cell.

    fontforge -quiet -script scripts/sfmono/apply_icon_scale.py <in.otf> <plan.json> <out.otf>
"""
import json
import sys

import fontforge
import psMat

IN, PLAN, OUT = sys.argv[1:4]

font = fontforge.open(IN)
plan = json.load(open(PLAN))

by_uni = {}
for g in font.glyphs():
    if g.unicode is not None and g.unicode >= 0:
        by_uni.setdefault(g.unicode, g)
    for alt in (g.altuni or ()):
        by_uni.setdefault(alt[0], g)

n = 0
for cphex, scale in plan.items():
    g = by_uni.get(int(cphex, 16))
    if g is None or scale >= 1.0:
        continue
    xmin, ymin, xmax, ymax = g.boundingBox()
    if xmax <= xmin:
        continue
    cx, cy = (xmin + xmax) / 2.0, (ymin + ymax) / 2.0
    m = psMat.compose(psMat.translate(-cx, -cy),
                      psMat.compose(psMat.scale(scale), psMat.translate(cx, cy)))
    g.transform(m)   # advance width left unchanged: icon shrinks in place
    n += 1

font.generate(OUT)
font.close()
print(f"[apply_icon_scale] scaled {n} glyphs -> {OUT}")
