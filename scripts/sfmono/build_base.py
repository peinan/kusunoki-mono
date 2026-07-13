"""P1: SF Mono Square base = SF Mono (Latin, CFF) + Migu 1M (JP), reproducing
delphinus's SF Mono Square method.

    fontforge -quiet -script scripts/sfmono/build_base.py <sf_mono.otf> <migu.ttf> <out.otf> <style>

- SF Mono is condensed uniformly ×(1024/1266)=0.809 to the square half-cell
  (advance 1024; a full-width CJK glyph = 2048 = one em = a square).
- Migu 1M provides kana / kanji / CJK punctuation: em 1000→2048, scaled ×0.82
  (delphinus's MIGU1M_SCALE), centred in the full-width cell (half-width katakana
  U+FF61–FFA0 in the half cell). For italic the JP is skewed to SF Mono's angle.
- Nerd icons are added AFTER this by the official nerd-fonts font-patcher.
- LINE Seed swap, GSC italic graft, ligatures come in later phases.

Knobs (env): HALF (1024 square / 1266 native), JP_SCALE (Migu size, 0.82),
JP_DY (vertical nudge at 2048 UPM).
"""
import math
import os
import sys

import fontforge
import psMat

SF, JP, OUT, STYLE = sys.argv[1:5]

EM = 2048
SF_NATIVE_ADV = 1266
HALF = int(os.environ.get("HALF", "1024"))
FULL = 2 * HALF
SF_SCALE = HALF / float(SF_NATIVE_ADV)
JP_SCALE = float(os.environ.get("JP_SCALE", "0.82"))
JP_DY = float(os.environ.get("JP_DY", "0"))
is_italic = "Italic" in STYLE

JP_RANGES = [
    (0x2E80, 0x2FDF),   # CJK radicals supplement + Kangxi radicals
    (0x3000, 0x30FF),   # CJK symbols/punct, hiragana, katakana
    (0x31F0, 0x31FF),   # katakana phonetic ext
    (0x3400, 0x4DBF),   # CJK ext A
    (0x4E00, 0x9FFF),   # CJK unified
    (0xF900, 0xFAFF),   # CJK compat ideographs
    (0xFF00, 0xFFEF),   # halfwidth/fullwidth forms
]
HALFWIDTH_KANA = (0xFF61, 0xFFA0)   # half-width katakana -> HALF cell


def in_jp(u):
    return u is not None and u >= 0 and any(lo <= u <= hi for lo, hi in JP_RANGES)


def keep_jp(g):
    if in_jp(g.unicode):
        return True
    for alt in (g.altuni or ()):
        if in_jp(alt[0]):
            return True
    return False


def is_halfkana(u):
    return u is not None and HALFWIDTH_KANA[0] <= u <= HALFWIDTH_KANA[1]


# Symbols SF Mono lacks (※, arrows, math, dingbats, Roman numerals, …) are pulled
# from Migu so they render in-font at Migu size instead of falling back to a huge
# mismatched system glyph — matching SF Mono Square. Structural cell-filling glyphs
# (box drawing 2500-257F, blocks 2580-259F, braille 2800-28FF) are left to SF Mono /
# the nerd patcher and excluded here.
SYMBOL_FILL_RANGES = [
    (0x00A0, 0x00FF), (0x2000, 0x24FF), (0x25A0, 0x27BF),
    (0x2900, 0x2BFF), (0x2E00, 0x2E7F),
]


def in_symbolfill(u):
    return u is not None and u >= 0 and any(lo <= u <= hi for lo, hi in SYMBOL_FILL_RANGES)


def strip_layout(font):
    # Only the outlines are wanted; dropping GSUB/GPOS avoids a warning flood
    # (dangling lookup refs after glyph pruning) that makes generate crawl.
    for lk in list(font.gsub_lookups) + list(font.gpos_lookups):
        font.removeLookup(lk)


sf = fontforge.open(SF)
italic_angle = abs(sf.italicangle) if is_italic else 0.0
if is_italic and italic_angle < 0.1:
    italic_angle = 10.0
rad = math.radians(italic_angle)
print(f"[build_base] {STYLE} HALF={HALF} FULL={FULL} SF_SCALE={SF_SCALE:.4f} "
      f"JP_SCALE={JP_SCALE} JP_DY={JP_DY} italic={italic_angle:.1f}deg")

# --- SF Mono -> square half-cell ---
if abs(SF_SCALE - 1.0) > 1e-6:
    for g in sf.glyphs():
        w = g.width
        g.transform(psMat.scale(SF_SCALE, SF_SCALE))
        if w > 0:
            g.width = HALF

# --- Migu JP: em->2048, keep JP only, scale, (italic) skew, centre in the cell ---
jp = fontforge.open(JP)
if jp.em != EM:
    jp.em = EM
strip_layout(jp)

sf_unicodes = set()
for g in sf.glyphs():
    if g.unicode is not None and g.unicode >= 0:
        sf_unicodes.add(g.unicode)
    for alt in (g.altuni or ()):
        sf_unicodes.add(alt[0])


def keep(g):  # JP glyphs, plus symbols SF Mono is missing (filled from Migu)
    return keep_jp(g) or (in_symbolfill(g.unicode) and g.unicode not in sf_unicodes)


drop = [g.glyphname for g in jp.glyphs() if not keep(g)]
for name in drop:
    if name in jp:
        jp.removeGlyph(name)

# Visible full-width space (the SF Mono Square / Ricty idea): U+3000 becomes the
# overlap of a ballot box (☐ U+2610) and a heavy cross (✚ U+271A) — a faint mark
# so a full-width space is visible. Scaled and centred with the rest of the JP below.
jp_unis = {g.unicode for g in jp.glyphs() if g.unicode is not None and g.unicode >= 0}
if {0x2610, 0x271A, 0x3000} <= jp_unis:
    jp.selection.select(("unicode",), 0x2610); jp.copy()
    jp.selection.select(("unicode",), 0x3000); jp.paste()
    jp.selection.select(("unicode",), 0x271A); jp.copy()
    jp.selection.select(("unicode",), 0x3000); jp.pasteInto()
    jp.selection.select(("unicode",), 0x3000); jp.intersect()
    print("[build_base] visible full-width space (U+3000 = ☐ ∩ ✚)")

kept = 0
for g in jp.glyphs():
    cell = HALF if is_halfkana(g.unicode) else FULL
    g.transform(psMat.scale(JP_SCALE, JP_SCALE))
    if is_italic:
        g.transform(psMat.skew(rad))
    xmin, ymin, xmax, ymax = g.boundingBox()
    if xmax > xmin:
        g.transform(psMat.translate((cell - (xmin + xmax)) / 2.0, JP_DY))
    g.width = cell
    kept += 1

tmp = OUT + ".jp.otf"
jp.generate(tmp)
jp.close()
sf.mergeFonts(tmp)
os.remove(tmp)

subfamily = {"Regular": "Regular", "Bold": "Bold",
             "Italic": "Italic", "BoldItalic": "Bold Italic"}[STYLE]
sf.familyname = "Kusunoki Mono"
sf.fontname = "KusunokiMono-" + STYLE
sf.fullname = "Kusunoki Mono" + ("" if subfamily == "Regular" else " " + subfamily)

# Square line box (baseline-to-baseline = em = FULL) so the base is square in
# both cell width and line height, matching SF Mono Square (1638/-410 at 2048).
# The nerd patch (P2) sizes icons against this box, so it must be the final,
# shipped metric here — otherwise icons get sized to SF Mono's native 2444 box
# and then shipped in the 2048 box, making Powerline separators overflow the
# line. finalize.py re-affirms the same values.
sf.os2_typoascent, sf.os2_typodescent, sf.os2_typolinegap = 1638, -410, 0
sf.os2_winascent, sf.os2_windescent = 1638, 410
sf.hhea_ascent, sf.hhea_descent, sf.hhea_linegap = 1638, -410, 0
sf.os2_use_typo_metrics = 1
sf.generate(OUT)
sf.close()
print(f"[build_base] merged {kept} Migu JP glyphs -> {OUT}")
