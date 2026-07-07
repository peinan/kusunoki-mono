#!/usr/bin/env python3
"""Transform LINE Seed JP (+ Nerd Fonts symbols) geometry for one style.

Run under FontForge:

    fontforge -quiet -script merge.py <style> <out_jp_ttf>

Reads configuration from the environment (exported by config.sh) and writes the
"jp half": LINE Seed JP rescaled to TARGET_EM, width-normalized to the HALF/FULL
cell, optionally skewed for italic, with Nerd symbols merged in. Deduplication
against Iosevka and the final union happen later in fix.py (fontTools) — this
stage only touches BIZ and Nerd so that Iosevka passes through untouched.
"""
import sys
import os
import math

import fontforge
import psMat


def env(key, default=None):
    val = os.environ.get(key, default)
    if val is None:
        raise SystemExit(f"merge.py: missing environment variable {key}")
    return val


TARGET_EM = int(env("TARGET_EM"))
WIDTH_EM = float(env("WIDTH_EM"))
HALF = round(WIDTH_EM * TARGET_EM)
FULL = 2 * HALF
ITALIC_ANGLE = float(env("ITALIC_ANGLE"))
VISUALIZE_ZENKAKU = env("VISUALIZE_ZENKAKU_SPACE", "1") == "1"
NERD = env("NERD_FONTS", "1") == "1"
SOURCES = env("SOURCES_DIR")
CJK_Y_SCALE = float(env("CJK_Y_SCALE", "1.0"))
CJK_Y_SHIFT = float(env("CJK_Y_SHIFT", "0"))

style = sys.argv[1]
out_jp = sys.argv[2]
is_italic = "Italic" in style
is_bold = "Bold" in style

jp_src = os.path.join(
    SOURCES, "lineseed-jp",
    "LINESeedJP-Bold.ttf" if is_bold else "LINESeedJP-Regular.ttf",
)


def rescale_em(font, em):
    if font.em != em:
        font.em = em  # rescales outlines + metrics


def set_width_centered(glyph, target):
    if glyph.width != target:
        glyph.transform(psMat.translate((target - glyph.width) / 2.0, 0))
        glyph.width = target


print(f"[merge.py] style={style} HALF={HALF} FULL={FULL} em={TARGET_EM}")

jp = fontforge.open(jp_src)
rescale_em(jp, TARGET_EM)

# --- vertical harmony (CJK only; tune via config.sh after inspecting specimen) ---
if CJK_Y_SCALE != 1.0 or CJK_Y_SHIFT != 0:
    vt = psMat.compose(psMat.scale(1.0, CJK_Y_SCALE), psMat.translate(0, CJK_Y_SHIFT))
    for g in jp.glyphs():
        if g.isWorthOutputting():
            g.transform(vt)

# --- italic: skew each glyph about its OWN vertical center (CJK only; icons stay
#     upright since they are merged afterwards). Centering per glyph keeps every
#     kana/kanji horizontally centered in its cell, regardless of its height. ---
if is_italic:
    rad = math.radians(ITALIC_ANGLE)
    tan = math.tan(rad)
    jp.italicangle = -ITALIC_ANGLE
    for g in jp.glyphs():
        if not g.isWorthOutputting():
            continue
        w = g.width
        xmin, ymin, xmax, ymax = g.boundingBox()
        cy = (ymin + ymax) / 2.0
        g.transform(psMat.compose(psMat.skew(rad), psMat.translate(-tan * cy, 0)))
        g.width = w

# --- merge Nerd Fonts symbols (single-width, forced to HALF) ---
if NERD:
    nerd_src = os.path.join(SOURCES, "nerd", "SymbolsNerdFontMono-Regular.ttf")
    nf = fontforge.open(nerd_src)
    rescale_em(nf, TARGET_EM)
    for g in nf.glyphs():
        if g.isWorthOutputting() and g.width != 0:
            set_width_centered(g, HALF)
    tmp_nerd = out_jp + ".nerd.ttf"
    nf.generate(tmp_nerd)
    nf.close()
    jp.mergeFonts(tmp_nerd)
    os.remove(tmp_nerd)

# --- width normalization: full-width -> FULL, half-width -> HALF, both centered ---
half_native = TARGET_EM // 2
threshold = half_native * 1.5
for g in jp.glyphs():
    if not g.isWorthOutputting() or g.width == 0:
        continue
    target = FULL if g.width > threshold else HALF
    set_width_centered(g, target)

# --- visualize the ideographic space U+3000 as a faint bordered box ---
if VISUALIZE_ZENKAKU:
    try:
        g = jp[0x3000]
        g.clear()
        pen = g.glyphPen()
        x0, x1 = FULL * 0.14, FULL * 0.86
        y0, y1 = -TARGET_EM * 0.02, TARGET_EM * 0.60
        t = TARGET_EM * 0.028
        # outer rectangle (clockwise)
        pen.moveTo((x0, y0)); pen.lineTo((x1, y0)); pen.lineTo((x1, y1)); pen.lineTo((x0, y1)); pen.closePath()
        # inner rectangle (counter-clockwise) -> leaves a thin frame
        pen.moveTo((x0 + t, y0 + t)); pen.lineTo((x0 + t, y1 - t)); pen.lineTo((x1 - t, y1 - t)); pen.lineTo((x1 - t, y0 + t)); pen.closePath()
        pen = None
        g.width = FULL
        g.correctDirection()
    except Exception as exc:  # noqa: BLE001 - cosmetic, never fatal
        print(f"[merge.py] U+3000 visualization skipped: {exc}")

jp.generate(out_jp)
jp.close()
print(f"[merge.py] wrote {out_jp}")
