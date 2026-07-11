"""Phase 2: replace SFMS's Migu Japanese with LINE Seed JP (square-grid fit),
keeping Migu for codepoints LINE Seed lacks. Runs on any of the 4 base styles.

    uv run --with fonttools python scripts/build_phase2_jp.py BASE OUT JPSRC ITALIC FAMILY SUBFAMILY

Only Hiragana/Katakana/Kanji (+CJK punctuation) codepoints present in BOTH fonts
are replaced; everything else (Latin, symbols, Nerd, rare Migu-only kanji, the
combined italic letters) is untouched. LINE Seed glyphs are scaled to Migu's CJK
size, centred in the SFMS cell, vertically aligned to Migu, and (for italic)
skewed to SFMS's 10 deg. Advance is kept = the SFMS cell so columns stay aligned.
"""
import sys, math
from fontTools.ttLib import TTFont
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.qu2cuPen import Qu2CuPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.misc.transform import Transform

BASE, OUT, JPSRC = sys.argv[1], sys.argv[2], sys.argv[3]
ITALIC = sys.argv[4] == "1"
FAMILY, SUBFAMILY = sys.argv[5], sys.argv[6]
SKEW = math.radians(10.0)

RANGES = [(0x3040,0x309F),(0x30A0,0x30FF),(0x31F0,0x31FF),
          (0x3400,0x4DBF),(0x4E00,0x9FFF),(0x3001,0x303F)]  # kana, kanji, CJK punct (skip U+3000)

def bbox(gs, gname, t):
    p = BoundsPen(None); rec = DecomposingRecordingPen(gs); gs[gname].draw(rec)
    rec.replay(TransformPen(p, t)); return rec, p.bounds

tgt = TTFont(BASE)
jp = TTFont(JPSRC)
tgt_cmap, jp_cmap = tgt.getBestCmap(), jp.getBestCmap()
jp_gs = jp.getGlyphSet()
jp_upm = jp["head"].unitsPerEm
tgt_upm = tgt["head"].unitsPerEm
hmtx = tgt["hmtx"]
cff = tgt["CFF "].cff; top = cff[cff.fontNames[0]]
cs, priv, gsubrs = top.CharStrings, top.Private, top.GlobalSubrs

# --- derive scale + vertical shift from Migu(target) vs LINE Seed on 日国永 ----
def tgt_h(ch):
    gn = tgt_cmap.get(ord(ch)); g = tgt.getGlyphSet()
    p = BoundsPen(g); g[gn].draw(p); return p.bounds
def jp_h(ch):
    gn = jp_cmap.get(ord(ch)); p = BoundsPen(jp_gs); jp_gs[gn].draw(p); return p.bounds
ratios, tcy, scy = [], [], []
for ch in "日国永":
    tb, jb = tgt_h(ch), jp_h(ch)
    ratios.append((tb[3]-tb[1])/(jb[3]-jb[1]))
    tcy.append((tb[1]+tb[3])/2); scy.append((jb[1]+jb[3])/2)
S = sorted(ratios)[1]                       # median height ratio (~1.685)
DY = (sum(tcy)/3) - (sum(scy)/3)*S          # align CJK centre to Migu
tan = math.tan(SKEW)
print(f"[{SUBFAMILY}] scale={S:.4f} dy={DY:.1f} italic={ITALIC}")

covered = 0
for lo, hi in RANGES:
    for cp in range(lo, hi+1):
        sname, tname = jp_cmap.get(cp), tgt_cmap.get(cp)
        if not sname or not tname or tname not in cs:
            continue
        adv = hmtx[tname][0]
        rec = DecomposingRecordingPen(jp_gs); jp_gs[sname].draw(rec)
        b1 = BoundsPen(None); rec.replay(TransformPen(b1, Transform(S,0,0,S,0,0)))
        if not b1.bounds:
            continue
        cy_s = (b1.bounds[1]+b1.bounds[3])/2
        yx = tan*S if ITALIC else 0.0
        e0 = -tan*cy_s if ITALIC else 0.0
        b2 = BoundsPen(None); rec.replay(TransformPen(b2, Transform(S,0,yx,S,e0,0)))
        cx2 = (b2.bounds[0]+b2.bounds[2])/2
        M = Transform(S, 0, yx, S, e0 + (adv/2.0 - cx2), DY)
        pen = T2CharStringPen(adv, None)
        rec.replay(TransformPen(Qu2CuPen(pen, max_err=1.0, reverse_direction=True), M))
        cs[tname] = pen.getCharString(private=priv, globalSubrs=gsubrs)
        bp = BoundsPen(None); rec.replay(TransformPen(bp, M))
        hmtx[tname] = (adv, int(round(bp.bounds[0])) if bp.bounds else 0)
        covered += 1

n = tgt["name"]
full = FAMILY if SUBFAMILY == "Regular" else f"{FAMILY} {SUBFAMILY}"
ps = f"{FAMILY.replace(' ','')}-{SUBFAMILY.replace(' ','')}"
for nid, val in {1:FAMILY,2:SUBFAMILY,4:full,6:ps,16:FAMILY,17:SUBFAMILY}.items():
    n.setName(val, nid, 3, 1, 0x409)
tgt.save(OUT)
print(f"[{SUBFAMILY}] replaced {covered} JP glyphs with LINE Seed -> {OUT}")
