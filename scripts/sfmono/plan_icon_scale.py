# /// script
# requires-python = ">=3.11"
# dependencies = ["fonttools>=4.50", "pillow>=10"]
# ///
"""Plan per-glyph downscales so icons that are TALLER than the SF Mono Square
reference shrink to match it — but ONLY when both fonts draw the SAME glyph
(icon sets drift between nerd-fonts versions; resizing a different drawing to
another's size is meaningless). Sameness is decided by rasterizing each glyph,
cropping to its ink box, normalizing, and requiring a high mask IoU.

    uv run scripts/sfmono/plan_icon_scale.py <patched.otf> <sfms_ref.otf> <out.json> [min_diff=2] [iou=0.6]

Emits {"CPHEX": scale(<1), ...}. Build-time only; nothing SFMS-derived is committed.
"""
import json
import sys
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen
from PIL import Image, ImageFont, ImageDraw

IN, REF, OUT = sys.argv[1:4]
MIN_DIFF = float(sys.argv[4]) if len(sys.argv) > 4 else 2.0
IOU_MIN = float(sys.argv[5]) if len(sys.argv) > 5 else 0.6

# candidate ranges: nerd PUA + text symbols, EXCLUDING structural glyphs that
# must fill the whole cell (Powerline E0A0-E0D7, Box/Blocks 2500-259F, Braille).
CAND = [(0x2000, 0x24FF), (0x25A0, 0x27FF), (0x2900, 0x2E7F),
        (0xE000, 0xE09F), (0xE0D8, 0xF8FF), (0xF0000, 0xF2000)]

def in_cand(cp):
    return any(lo <= cp <= hi for lo, hi in CAND)

def heights(path):
    f = TTFont(path)
    cmap = f.getBestCmap()
    gs = f.getGlyphSet()
    upm = f["head"].unitsPerEm
    s = 2048.0 / upm
    out = {}
    for cp, gn in cmap.items():
        if not in_cand(cp):
            continue
        pen = BoundsPen(gs)
        try:
            gs[gn].draw(pen)
        except Exception:
            continue
        if pen.bounds is None:
            continue
        out[cp] = (pen.bounds[3] - pen.bounds[1]) * s / 2048 * 100
    return out

N, CAN = 64, 320
def mask(font, cp):
    img = Image.new("L", (CAN, CAN), 0)
    ImageDraw.Draw(img).text((CAN // 2, CAN // 2), chr(cp), font=font, fill=255, anchor="mm")
    bb = img.getbbox()
    if not bb:
        return None
    crop = img.crop(bb).resize((N, N), Image.LANCZOS).load()
    return [1 if crop[x, y] > 64 else 0 for y in range(N) for x in range(N)]

def iou(a, b):
    if a is None or b is None:
        return 0.0
    inter = sum(1 for x, y in zip(a, b) if x and y)
    uni = sum(1 for x, y in zip(a, b) if x or y)
    return inter / uni if uni else 0.0

kh, sh = heights(IN), heights(REF)
kfont = ImageFont.truetype(IN, 200)
sfont = ImageFont.truetype(REF, 200)

plan = {}
diff_skipped = 0
considered = 0
for cp, k in kh.items():
    s = sh.get(cp)
    if s is None:
        continue
    if k - s < MIN_DIFF:          # only shrink glyphs bigger than the reference
        continue
    considered += 1
    if iou(mask(kfont, cp), mask(sfont, cp)) < IOU_MIN:  # different drawing -> leave it
        diff_skipped += 1
        continue
    plan["%04X" % cp] = round(s / k, 4)

with open(OUT, "w") as f:
    json.dump(plan, f)
print(f"[plan_icon_scale] ours-bigger>= {MIN_DIFF}%: {considered}  "
      f"same-glyph->scale: {len(plan)}  different-glyph->skip: {diff_skipped}  -> {OUT}")
