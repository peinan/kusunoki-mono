# /// script
# requires-python = ">=3.10"
# dependencies = ["fonttools>=4.50"]
# ///
"""Merge Iosevka (untouched) with the transformed BIZ/Nerd 'jp' half, fix tables.

    uv run fix.py <iosevka_ttf> <jp_ttf> <out_ttf> <style>

Iosevka is passed to the merger first, so on any codepoint conflict Iosevka wins
and its GSUB (ligatures) is preserved. The jp half is first subset to only the
codepoints Iosevka does NOT cover (dedup), then merged. Finally the name / OS2 /
post / vertical-metric tables are set for a coherent Japanese monospace font.
"""
import os
import sys

from fontTools.ttLib import TTFont
from fontTools.merge import Merger
from fontTools import subset

iose_path, jp_path, out_path, style = sys.argv[1:5]

TARGET_EM = int(os.environ["TARGET_EM"])
WIDTH_EM = float(os.environ["WIDTH_EM"])
HALF = round(WIDTH_EM * TARGET_EM)
FAMILY = os.environ["FAMILY"]
VERSION = os.environ["VERSION"]
ITALIC_ANGLE = float(os.environ["ITALIC_ANGLE"])

is_italic = "Italic" in style
is_bold = "Bold" in style

SUBFAMILY = {
    "Regular": "Regular",
    "Bold": "Bold",
    "Italic": "Italic",
    "BoldItalic": "Bold Italic",
}[style]

COPYRIGHT = (
    "Kusunoki Mono is built from Iosevka (© Belleve Invis, OFL-1.1), "
    "BIZ UDGothic (© Morisawa Inc. / Type Bank, OFL-1.1), "
    "and Nerd Fonts (© Ryan L McIntyre, MIT)."
)
LICENSE_DESC = "This Font Software is licensed under the SIL Open Font License, Version 1.1."
LICENSE_URL = "https://openfontlicense.org"


def cmap_unicodes(font):
    cps = set()
    for t in font["cmap"].tables:
        if t.isUnicode():
            cps.update(t.cmap.keys())
    return cps


# --- gather codepoints, then dedup the jp half against Iosevka --------------
iose = TTFont(iose_path)
jp = TTFont(jp_path)
iose_cps = cmap_unicodes(iose)
jp_cps = cmap_unicodes(jp)
keep = jp_cps - iose_cps
iose.close()
if not keep:
    raise SystemExit("fix.py: jp half has nothing left after dedup against Iosevka")

# Drop tables that make the merge fragile or that Iosevka should own:
#  - vertical writing (vhea/vmtx/VORG): unused in a horizontal mono font, and
#    present in only one font -> breaks fontTools' table merger.
#  - FFTM/DSIG/meta: FontForge / signature cruft.
#  - all OpenType layout is dropped below via layout_features=[]: Iosevka provides
#    every feature (including ligatures), so keeping BIZ's layout only invites
#    conflicts. We keep the CJK glyphs, not BIZ's GSUB/GPOS.
for tag in ("vhea", "vmtx", "VORG", "FFTM", "DSIG", "meta"):
    if tag in jp:
        del jp[tag]

ss = subset.Subsetter()
ss.options.layout_features = []          # drop BIZ layout; Iosevka owns all layout
ss.options.name_IDs = ["*"]
ss.options.name_legacy = True
ss.options.name_languages = ["*"]
ss.options.notdef_outline = True
ss.options.glyph_names = True
ss.options.recalc_bounds = True
ss.populate(unicodes=keep)
ss.subset(jp)
jp_sub = jp_path + ".sub.ttf"
jp.save(jp_sub)
jp.close()

# --- merge (Iosevka first => wins conflicts, keeps ligature GSUB) -----------
merged = Merger().merge([iose_path, jp_sub])

# --- vertical metrics: cover both Latin and CJK extents ---------------------
mi, mj = TTFont(iose_path), TTFont(jp_path)
asc = max(mi["OS/2"].sTypoAscender, mj["OS/2"].sTypoAscender)
desc = min(mi["OS/2"].sTypoDescender, mj["OS/2"].sTypoDescender)
win_asc = max(mi["OS/2"].usWinAscent, mj["OS/2"].usWinAscent)
win_desc = max(mi["OS/2"].usWinDescent, mj["OS/2"].usWinDescent)
mi.close()
mj.close()

# --- name table -------------------------------------------------------------
name = merged["name"]
full_name = FAMILY if SUBFAMILY == "Regular" else f"{FAMILY} {SUBFAMILY}"
ps_name = f"{FAMILY.replace(' ', '')}-{style}"
values = {
    0: COPYRIGHT,
    1: FAMILY if SUBFAMILY in ("Regular", "Bold", "Italic", "Bold Italic") else FAMILY,
    2: SUBFAMILY if SUBFAMILY in ("Regular", "Bold", "Italic", "Bold Italic") else "Regular",
    3: f"{VERSION};{ps_name}",
    4: full_name,
    5: f"Version {VERSION}",
    6: ps_name,
    13: LICENSE_DESC,
    14: LICENSE_URL,
    16: FAMILY,
    17: SUBFAMILY,
}
# RIBBI: nameID 1/2 must keep the 4 styles groupable. Bold Italic -> family
# "Kusunoki Mono", subfamily "Bold Italic" is not RIBBI-legal for ID 1/2, so
# fold weight into the family for the two italic-bold members.
if style == "BoldItalic":
    values[1] = FAMILY
    values[2] = "Bold Italic"
for nid, val in values.items():
    name.removeNames(nameID=nid)
    name.setName(val, nid, 3, 1, 0x409)  # Windows / Unicode BMP / en-US
    name.setName(val, nid, 1, 0, 0)      # Mac / Roman / en

# --- OS/2 -------------------------------------------------------------------
os2 = merged["OS/2"]
os2.sTypoAscender, os2.sTypoDescender, os2.sTypoLineGap = asc, desc, 0
os2.usWinAscent, os2.usWinDescent = win_asc, win_desc
os2.xAvgCharWidth = HALF
os2.usWeightClass = 700 if is_bold else 400
os2.ulCodePageRange1 |= (1 << 0)    # Latin 1 (CP1252)
os2.ulCodePageRange1 |= (1 << 17)   # Japanese (CP932) -> "this is a Japanese font"
os2.recalcUnicodeRanges(merged)
# PANOSE: latin text, normal sans, monospaced
os2.panose.bFamilyType = 2
os2.panose.bSerifStyle = 11
os2.panose.bProportion = 9
fs = (1 << 7)                        # USE_TYPO_METRICS
if is_bold:
    fs |= (1 << 5)
if is_italic:
    fs |= (1 << 0)
if not (is_bold or is_italic):
    fs |= (1 << 6)                  # REGULAR
os2.fsSelection = fs

# --- hhea (match typo metrics) ----------------------------------------------
merged["hhea"].ascent, merged["hhea"].descent, merged["hhea"].lineGap = asc, desc, 0

# --- head.macStyle ----------------------------------------------------------
mac = 0
if is_bold:
    mac |= 0x01
if is_italic:
    mac |= 0x02
merged["head"].macStyle = mac

# --- post -------------------------------------------------------------------
merged["post"].isFixedPitch = 1
merged["post"].italicAngle = -ITALIC_ANGLE if is_italic else 0.0

merged.save(out_path)
os.remove(jp_sub)
print(f"[fix.py] wrote {out_path}  (kept {len(keep)} CJK/symbol codepoints)")
