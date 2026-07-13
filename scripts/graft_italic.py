# /// script
# requires-python = ">=3.11"
# dependencies = ["fonttools>=4.50"]
# ///
"""P3: graft Google Sans Code true-italic letters into an italic style.

    uv run scripts/graft_italic.py <base_italic.otf> <gsc_italic_vf.ttf> <out.otf> <gsc_wght>

SF Mono's italic is kept for everything except 14 lowercase letters
(a b c d e f i j k l p v y z), which are replaced with Google Sans Code's true
italic. Each grafted letter is x-height-matched to the base and positioned to the
median ink-centre offset of the SF Mono italic letters that STAY (SF Mono italic
sits its ink right-of-centre, so advance-box centring would break the monospace
rhythm). GSC is instanced at a tuned weight (thinner) to match SF Mono's stems.
"""
import sys

from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.qu2cuPen import Qu2CuPen
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.transformPen import TransformPen
from fontTools.misc.transform import Transform

BASE, GSC_VF, OUT, WGHT = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4])
GSC_LETTERS = "abcdefijklpvyz"        # the rest (g h m n o q r s t u w x, caps, symbols) stay SF Mono


def xheight(f):
    gs, cmap = f.getGlyphSet(), f.getBestCmap()
    p = BoundsPen(gs)
    gs[cmap[ord("x")]].draw(p)
    return p.bounds[3] - p.bounds[1]


def mono_adv(f):
    return f["hmtx"][f.getBestCmap()[ord("M")]][0]


def median(vals):
    s = sorted(vals)
    n = len(s)
    return 0 if n == 0 else (s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2)


def ink_offset(tgt):
    """Median ink-centre offset (from the cell centre) of the SF Mono italic
    lowercase letters that stay — grafted glyphs must match this offset."""
    gs, cmap, hmtx = tgt.getGlyphSet(), tgt.getBestCmap(), tgt["hmtx"]
    offs = []
    for c in "ghmnoqrstuwx":
        gn = cmap.get(ord(c))
        if not gn:
            continue
        p = BoundsPen(gs)
        gs[gn].draw(p)
        if p.bounds:
            xmin, _, xmax, _ = p.bounds
            offs.append((xmin + xmax) / 2 - hmtx[gn][0] / 2.0)
    return median(offs)


tgt = TTFont(BASE)
gsc = instancer.instantiateVariableFont(TTFont(GSC_VF), {"wght": WGHT}, inplace=False)
src_gs, src_cmap = gsc.getGlyphSet(), gsc.getBestCmap()
tgt_cmap = tgt.getBestCmap()

S = xheight(tgt) / xheight(gsc)
adv = mono_adv(tgt)
off = ink_offset(tgt)
cff = tgt["CFF "].cff
top = cff[cff.fontNames[0]]
cs, priv, gsubrs = top.CharStrings, top.Private, top.GlobalSubrs
hmtx = tgt["hmtx"]

n = 0
for ch in GSC_LETTERS:
    cp = ord(ch)
    sname, tname = src_cmap.get(cp), tgt_cmap.get(cp)
    if not sname or not tname or tname not in cs:
        continue
    rec = DecomposingRecordingPen(src_gs)
    src_gs[sname].draw(rec)
    sb = BoundsPen(None)
    rec.replay(TransformPen(sb, Transform().scale(S)))
    if not sb.bounds:
        continue
    icx = (sb.bounds[0] + sb.bounds[2]) / 2.0
    dx = (adv / 2.0 + off) - icx
    xform = Transform().translate(dx, 0).scale(S)
    pen = T2CharStringPen(adv, None)
    rec.replay(TransformPen(Qu2CuPen(pen, max_err=0.5, reverse_direction=True), xform))
    cs[tname] = pen.getCharString(private=priv, globalSubrs=gsubrs)
    bp = BoundsPen(None)
    rec.replay(TransformPen(bp, xform))
    hmtx[tname] = (adv, int(round(bp.bounds[0])) if bp.bounds else 0)
    n += 1

tgt.save(OUT)
print(f"[graft_italic] grafted {n} GSC letters (wght={WGHT:.0f}) -> {OUT}")
