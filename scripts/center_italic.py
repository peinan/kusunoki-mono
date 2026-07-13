# /// script
# requires-python = ">=3.11"
# dependencies = ["fonttools>=4.50"]
# ///
"""Set the italic's Latin ink-offset (parameterised).

    ITALIC_INK_OFFSET=0.0 uv run scripts/center_italic.py <in.otf> <out.otf>

SF Mono's italic sits its ink right-of-centre (~+7.6% of the cell). This shifts
the ASCII (SF Mono) glyphs uniformly so their MEDIAN ink-offset equals
ITALIC_INK_OFFSET * cell — preserving SF Mono's relative sidebearings, only
removing/retargeting the global lean. JP and Nerd glyphs are already centred and
are left untouched.

  ITALIC_INK_OFFSET = 0.0    -> centred like the upright (default)
  ITALIC_INK_OFFSET = 0.076  -> keep SF Mono / SFMS native right-lean
"""
import os
import sys

from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.transformPen import TransformPen
from fontTools.misc.transform import Transform

IN, OUT = sys.argv[1], sys.argv[2]
TARGET_FRAC = float(os.environ.get("ITALIC_INK_OFFSET", "0.0"))

f = TTFont(IN)
cmap, gs, hmtx = f.getBestCmap(), f.getGlyphSet(), f["hmtx"]
cff = f["CFF "].cff
top = cff[cff.fontNames[0]]
cs, priv, gsubrs = top.CharStrings, top.Private, top.GlobalSubrs

adv = hmtx[cmap[ord("M")]][0]
offs = []
for lo, hi in ((0x41, 0x5A), (0x61, 0x7A)):            # A-Z, a-z
    for cp in range(lo, hi + 1):
        gn = cmap.get(cp)
        if not gn:
            continue
        bp = BoundsPen(gs)
        gs[gn].draw(bp)
        if bp.bounds:
            offs.append((bp.bounds[0] + bp.bounds[2]) / 2 - adv / 2.0)
offs.sort()
median = offs[len(offs) // 2] if offs else 0.0
shift = TARGET_FRAC * adv - median
print(f"median offset={median:+.0f}, target={TARGET_FRAC * adv:+.0f} -> shift={shift:+.0f}")

n = 0
for cp in range(0x21, 0x7F):                            # all ASCII printable (SF Mono)
    gn = cmap.get(cp)
    if not gn or gn not in cs:
        continue
    a = hmtx[gn][0]
    rec = DecomposingRecordingPen(gs)
    gs[gn].draw(rec)
    t = Transform().translate(shift, 0)
    pen = T2CharStringPen(a, None)
    rec.replay(TransformPen(pen, t))
    cs[gn] = pen.getCharString(private=priv, globalSubrs=gsubrs)
    bp = BoundsPen(None)
    rec.replay(TransformPen(bp, t))
    hmtx[gn] = (a, int(round(bp.bounds[0])) if bp.bounds else 0)
    n += 1
f.save(OUT)
print(f"[center_italic] shifted {n} ASCII glyphs (ITALIC_INK_OFFSET={TARGET_FRAC}) -> {OUT}")
