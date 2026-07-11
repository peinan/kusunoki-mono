"""Build PoC italic variants: graft {Iosevka, Google Sans Code} italic *letters*
into SF Mono Square's Italic / BoldItalic (letters only; digits/symbols/JP kept).

    uv run --with fonttools python scripts/build_poc_variants.py

Each source letter is x-height-matched to SFMS, re-centred in the 1024 half-cell,
quad->cubic, written as a CFF charstring. Baselines shared (y=0). Outputs 4 OTFs
under build/poc/ plus keeps family names distinct for side-by-side install.
"""
import os
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.qu2cuPen import Qu2CuPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.misc.transform import Transform

HOME = os.path.expanduser("~")
LETTERS = [ord(c) for c in
           "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"]


def xheight(font):
    gs, cmap = font.getGlyphSet(), font.getBestCmap()
    p = BoundsPen(gs); gs[cmap[ord("x")]].draw(p)
    return p.bounds[3] - p.bounds[1]


def mono_adv(font):
    return font["hmtx"][font.getBestCmap()[ord("M")]][0]


def graft(target_path, source_font, out_path, family):
    tgt = TTFont(target_path)
    src_gs, src_cmap = source_font.getGlyphSet(), source_font.getBestCmap()
    tgt_cmap = tgt.getBestCmap()

    S = xheight(tgt) / xheight(source_font)
    src_adv, tgt_adv = mono_adv(source_font), mono_adv(tgt)
    DX = (tgt_adv - src_adv * S) / 2.0
    xform = Transform().translate(DX, 0).scale(S)

    cff = tgt["CFF "].cff
    top = cff[cff.fontNames[0]]
    cs, priv, gsubrs = top.CharStrings, top.Private, top.GlobalSubrs
    hmtx = tgt["hmtx"]

    n = 0
    for cp in LETTERS:
        sname, tname = src_cmap.get(cp), tgt_cmap.get(cp)
        if not sname or not tname:
            continue
        rec = DecomposingRecordingPen(src_gs)
        src_gs[sname].draw(rec)
        pen = T2CharStringPen(tgt_adv, None)
        rec.replay(TransformPen(Qu2CuPen(pen, max_err=0.5, reverse_direction=True), xform))
        cs[tname] = pen.getCharString(private=priv, globalSubrs=gsubrs)
        bp = BoundsPen(None)
        rec.replay(TransformPen(bp, xform))
        hmtx[tname] = (tgt_adv, int(round(bp.bounds[0])) if bp.bounds else 0)
        n += 1

    name = tgt["name"]
    name.setName(family, 1, 3, 1, 0x409)
    name.setName(family, 4, 3, 1, 0x409)
    name.setName(family.replace(" ", ""), 6, 3, 1, 0x409)
    tgt.save(out_path)
    print(f"  {family}: grafted {n} (scale={S:.4f}, dx={DX:.1f}) -> {out_path}")


SFMS_ITALIC = os.path.join(HOME, "Library/Fonts/SFMonoSquare-RegularItalic.otf")
SFMS_BOLDITALIC = os.path.join(HOME, "Library/Fonts/SFMonoSquare-BoldItalic.otf")
IOSEVKA_I = "dist-0.5em/KusunokiMonoNFLG/KusunokiMonoNFLG-Italic.ttf"
IOSEVKA_BI = "dist-0.5em/KusunokiMonoNFLG/KusunokiMonoNFLG-BoldItalic.ttf"
GSC_ITALIC_VF = "sources/google-sans-code/GoogleSansCode-Italic[wght].ttf"

os.makedirs("build/poc", exist_ok=True)

print("Iosevka:")
graft(SFMS_ITALIC, TTFont(IOSEVKA_I), "build/poc/graft-Iosevka-Italic.otf", "SFMS Iosevka Italic")
graft(SFMS_BOLDITALIC, TTFont(IOSEVKA_BI), "build/poc/graft-Iosevka-BoldItalic.otf", "SFMS Iosevka BoldItalic")

print("Google Sans Code:")
gsc_r = instancer.instantiateVariableFont(TTFont(GSC_ITALIC_VF), {"wght": 400}, inplace=False)
gsc_b = instancer.instantiateVariableFont(TTFont(GSC_ITALIC_VF), {"wght": 700}, inplace=False)
graft(SFMS_ITALIC, gsc_r, "build/poc/graft-GSC-Italic.otf", "SFMS GSC Italic")
graft(SFMS_BOLDITALIC, gsc_b, "build/poc/graft-GSC-BoldItalic.otf", "SFMS GSC BoldItalic")
print("done")
