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
drop = [g.glyphname for g in jp.glyphs() if not keep_jp(g)]
for name in drop:
    if name in jp:
        jp.removeGlyph(name)

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
sf.generate(OUT)
sf.close()
print(f"[build_base] merged {kept} Migu JP glyphs -> {OUT}")
