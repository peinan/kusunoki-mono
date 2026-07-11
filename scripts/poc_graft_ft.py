"""PoC graft, fontTools-only: inject Iosevka italic *letters* into SFMS Italic.

    uv run --with fonttools python scripts/poc_graft_ft.py

Keeps SFMS's CFF pristine; only replaces A-Za-z charstrings. Each source letter
(1000 em, quadratic) is scaled to SFMS x-height (878/520), re-centred in the 1024
half-cell, converted quad->cubic, and written as a CFF T2 charstring. hmtx sets
the advance to 1024 (authoritative in OTF). Baseline shared (both at y=0).
"""
import os
from fontTools.ttLib import TTFont
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.qu2cuPen import Qu2CuPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.misc.transform import Transform

HOME = os.path.expanduser("~")
TARGET = os.path.join(HOME, "Library/Fonts/SFMonoSquare-RegularItalic.otf")
SOURCE = "dist-0.5em/KusunokiMonoNFLG/KusunokiMonoNFLG-Italic.ttf"
OUT = "build/poc/SFMSItalicGraftPoC-Italic.otf"

SFMS_X, SRC_X = 878.0, 520.0
S = SFMS_X / SRC_X            # x-height match (bridges em): 1.6885
SRC_ADV, TARGET_ADV = 500.0, 1024
DX = (TARGET_ADV - SRC_ADV * S) / 2.0
XFORM = Transform().translate(DX, 0).scale(S)   # scale first, then centre-shift

LETTERS = [ord(c) for c in
           "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"]

tgt = TTFont(TARGET)
src = TTFont(SOURCE)
src_gs = src.getGlyphSet()
src_cmap = src.getBestCmap()
tgt_cmap = tgt.getBestCmap()

cff = tgt["CFF "].cff
topDict = cff[cff.fontNames[0]]
charStrings = topDict.CharStrings
priv = topDict.Private
gsubrs = topDict.GlobalSubrs
hmtx = tgt["hmtx"]

grafted = 0
for cp in LETTERS:
    sname, tname = src_cmap.get(cp), tgt_cmap.get(cp)
    if not sname or not tname:
        print("skip U+%04X" % cp)
        continue
    rec = DecomposingRecordingPen(src_gs)   # flatten i/j composites to contours
    src_gs[sname].draw(rec)

    t2 = T2CharStringPen(TARGET_ADV, None)
    q = Qu2CuPen(t2, max_err=0.5, reverse_direction=True)  # TT->CFF winding
    rec.replay(TransformPen(q, XFORM))
    charStrings[tname] = t2.getCharString(private=priv, globalSubrs=gsubrs)

    bp = BoundsPen(src_gs)
    rec.replay(TransformPen(bp, XFORM))
    xmin = int(round(bp.bounds[0])) if bp.bounds else 0
    hmtx[tname] = (TARGET_ADV, xmin)
    grafted += 1

for rec in tgt["name"].names:
    pass
tgt["name"].setName("SFMS Italic Graft PoC", 1, 3, 1, 0x409)
tgt["name"].setName("SFMS Italic Graft PoC Italic", 4, 3, 1, 0x409)
tgt["name"].setName("SFMSItalicGraftPoC-Italic", 6, 3, 1, 0x409)

os.makedirs("build/poc", exist_ok=True)
tgt.save(OUT)
print("grafted %d letters -> %s (scale=%.4f, dx=%.1f)" % (grafted, OUT, S, DX))
