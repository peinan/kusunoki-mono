# /// script
# requires-python = ">=3.11"
# dependencies = ["fonttools>=4.50"]
# ///
"""P2: swap the square base's Noto Sans JP for LINE Seed JP where LINE Seed covers it.

    uv run scripts/sfmono/swap_lineseed.py <base.otf> <out.otf> <lineseed.ttf> <style>

Only kana / katakana / kanji / CJK punctuation present in BOTH the base and LINE
Seed are replaced; everything else (SF Mono Latin, digits, Nerd icons, and the rare
kanji LINE Seed lacks) keeps the base (Noto). Each LINE Seed glyph is scaled to the
base's CJK size (measured on 国永日), centred in the full-width cell, vertically
aligned, and — for italic — skewed to the base's italic angle. The advance is kept,
so columns stay aligned.

Note: `、`/`。` are centred here like every other CJK glyph; left-aligning them is
issue #4, handled in a later step.
"""
import math
import sys

from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.qu2cuPen import Qu2CuPen
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.transformPen import TransformPen
from fontTools.misc.transform import Transform

BASE, OUT, JPSRC, STYLE = sys.argv[1:5]
is_italic = "Italic" in STYLE

# kana, katakana (+phonetic ext), CJK ext-A, CJK unified, CJK punctuation (skip U+3000)
RANGES = [(0x3040, 0x309F), (0x30A0, 0x30FF), (0x31F0, 0x31FF),
          (0x3400, 0x4DBF), (0x4E00, 0x9FFF), (0x3001, 0x303F)]

tgt = TTFont(BASE)
jp = TTFont(JPSRC)
tgt_cmap, jp_cmap = tgt.getBestCmap(), jp.getBestCmap()
tgt_gs, jp_gs = tgt.getGlyphSet(), jp.getGlyphSet()
hmtx = tgt["hmtx"]
cff = tgt["CFF "].cff
top = cff[cff.fontNames[0]]
cs, priv, gsubrs = top.CharStrings, top.Private, top.GlobalSubrs

# Italic angle from the base (SF Mono's, preserved through the FontForge build);
# post.italicAngle is negative for a right-leaning slope, so negate for the skew.
ital = tgt["post"].italicAngle if is_italic else 0.0
tan = math.tan(math.radians(-ital))


def bounds(gs, cmap, ch):
    gn = cmap.get(ord(ch))
    if not gn:
        return None
    p = BoundsPen(gs)
    gs[gn].draw(p)
    return p.bounds


# Derive the LINE-Seed->base scale + vertical shift from reference kanji.
ratios, tcy, scy = [], [], []
for ch in "国永日":
    tb, jb = bounds(tgt_gs, tgt_cmap, ch), bounds(jp_gs, jp_cmap, ch)
    if not tb or not jb:
        continue
    ratios.append((tb[3] - tb[1]) / (jb[3] - jb[1]))
    tcy.append((tb[1] + tb[3]) / 2)
    scy.append((jb[1] + jb[3]) / 2)
if not ratios:
    raise SystemExit("swap_lineseed: no reference kanji shared by base and LINE Seed")
S = sorted(ratios)[len(ratios) // 2]
DY = (sum(tcy) / len(tcy)) - (sum(scy) / len(scy)) * S
print(f"[{STYLE}] scale={S:.4f} dy={DY:.1f} italic={ital:.1f}")

covered = 0
for lo, hi in RANGES:
    for cp in range(lo, hi + 1):
        sname, tname = jp_cmap.get(cp), tgt_cmap.get(cp)
        if not sname or not tname or tname not in cs:
            continue
        adv = hmtx[tname][0]
        rec = DecomposingRecordingPen(jp_gs)
        jp_gs[sname].draw(rec)
        b1 = BoundsPen(None)
        rec.replay(TransformPen(b1, Transform(S, 0, 0, S, 0, 0)))
        if not b1.bounds:
            continue
        cy_s = (b1.bounds[1] + b1.bounds[3]) / 2
        yx = tan * S if is_italic else 0.0
        e0 = -tan * cy_s if is_italic else 0.0
        b2 = BoundsPen(None)
        rec.replay(TransformPen(b2, Transform(S, 0, yx, S, e0, 0)))
        cx2 = (b2.bounds[0] + b2.bounds[2]) / 2
        M = Transform(S, 0, yx, S, e0 + (adv / 2.0 - cx2), DY)
        pen = T2CharStringPen(adv, None)
        rec.replay(TransformPen(Qu2CuPen(pen, max_err=1.0, reverse_direction=True), M))
        cs[tname] = pen.getCharString(private=priv, globalSubrs=gsubrs)
        bp = BoundsPen(None)
        rec.replay(TransformPen(bp, M))
        hmtx[tname] = (adv, int(round(bp.bounds[0])) if bp.bounds else 0)
        covered += 1

tgt.save(OUT)
print(f"[{STYLE}] replaced {covered} JP glyphs with LINE Seed -> {OUT}")
