# /// script
# requires-python = ">=3.11"
# dependencies = ["fonttools>=4.50"]
# ///
"""P4: finalize a built style — name table (RIBBI), OS/2, metrics, post.

    KM_VERSION=0.6.0 uv run scripts/finalize.py <in.otf> <out.otf> <style>

Makes the font a coherent, installable Japanese monospace: the 4 styles group
under one family "Kusunoki Mono", vertical metrics match SF Mono Square
(1638/-410 at 2048 UPM), PANOSE = monospaced sans, Latin + Japanese code pages.
The copyright/license note records that the font embeds Apple SF Mono and is a
personal, non-redistributable, non-OFL build.
"""
import os
import sys

from fontTools.ttLib import TTFont

IN, OUT, STYLE = sys.argv[1:4]
FAMILY = "Kusunoki Mono"
VERSION = os.environ.get("KM_VERSION", "0.6.0")
is_bold = "Bold" in STYLE
is_italic = "Italic" in STYLE
SUB = {"Regular": "Regular", "Bold": "Bold",
       "Italic": "Italic", "BoldItalic": "Bold Italic"}[STYLE]

COPYRIGHT = (
    "Kusunoki Mono (SF Mono Square edition) — a personal, locally built font. "
    "Built from Apple SF Mono (© Apple Inc.), Noto Sans JP (© The Noto Project Authors, OFL-1.1), "
    "LINE Seed JP (© LY Corporation, OFL-1.1), Google Sans Code (© Google LLC, OFL-1.1), "
    "and Nerd Fonts (© Ryan L McIntyre, MIT)."
)
LICENSE_DESC = (
    "Contains Apple SF Mono, which is licensed by Apple and may not be redistributed. "
    "This is a personal, locally built font for the builder's own use only — it is not "
    "distributed and is not covered by the SIL Open Font License."
)
LICENSE_URL = "https://github.com/peinan/kusunoki"

f = TTFont(IN)

# --- name table (RIBBI: all 4 styles under one family) ---
name = f["name"]
full = FAMILY if SUB == "Regular" else f"{FAMILY} {SUB}"
ps = f"{FAMILY.replace(' ', '')}-{STYLE}"
values = {
    0: COPYRIGHT, 1: FAMILY, 2: SUB, 3: f"{VERSION};{ps}", 4: full,
    5: f"Version {VERSION}", 6: ps, 13: LICENSE_DESC, 14: LICENSE_URL,
    16: FAMILY, 17: SUB,
}
for nid, val in values.items():
    name.removeNames(nameID=nid)
    name.setName(val, nid, 3, 1, 0x409)   # Windows / Unicode BMP / en-US
    name.setName(val, nid, 1, 0, 0)       # Mac / Roman / en

# --- OS/2 ---
os2 = f["OS/2"]
os2.sTypoAscender, os2.sTypoDescender, os2.sTypoLineGap = 1638, -410, 0
os2.usWinAscent, os2.usWinDescent = 1638, 410
os2.usWeightClass = 700 if is_bold else 400
os2.xAvgCharWidth = 1024
os2.panose.bFamilyType = 2       # latin text
os2.panose.bSerifStyle = 11      # normal sans
os2.panose.bProportion = 9       # monospaced
os2.panose.bLetterForm = 9 if is_italic else 2
fs = (1 << 7)                    # USE_TYPO_METRICS
if is_bold:
    fs |= (1 << 5)
if is_italic:
    fs |= (1 << 0)
if not (is_bold or is_italic):
    fs |= (1 << 6)               # REGULAR
os2.fsSelection = fs
os2.ulCodePageRange1 |= (1 << 0)     # Latin 1 (CP1252)
os2.ulCodePageRange1 |= (1 << 17)    # Japanese (CP932)
os2.recalcUnicodeRanges(f)
# fsType is left as inherited from SF Mono (embedding restriction preserved).

# --- hhea / head / post ---
f["hhea"].ascent, f["hhea"].descent, f["hhea"].lineGap = 1638, -410, 0
mac = 0
if is_bold:
    mac |= 0x01
if is_italic:
    mac |= 0x02
f["head"].macStyle = mac
f["post"].isFixedPitch = 1
f["post"].italicAngle = -10.0 if is_italic else 0.0

f.save(OUT)
print(f"[finalize] {full}  wght={os2.usWeightClass} fsSel={os2.fsSelection:#06x} -> {OUT}")
