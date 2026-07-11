"""Stamp a distinct, install-safe family name onto the 4 Phase-2 fonts.

    uv run --with fonttools python scripts/name_family.py "Family Name"

Sets RIBBI name records on BOTH Windows (3,1,0x409) and Mac (1,0,0) platforms and
removes the old SF Mono Square records, so the font installs as its own family
(no clash with the real SF Mono Square). Copyright (nameID 0) is left intact —
it still credits Apple + delphinus, correct for a personal derivative.
"""
import sys, glob, os
from fontTools.ttLib import TTFont

FAMILY = sys.argv[1]
STYLES = {  # file suffix -> (subfamily, macStyle, weight, italic)
    "Regular": ("Regular", 0, 400, False),
    "Bold": ("Bold", 1, 700, False),
    "Italic": ("Italic", 2, 400, True),
    "BoldItalic": ("Bold Italic", 3, 700, True),
}

for suffix, (sub, mac, wght, ital) in STYLES.items():
    path = f"build/poc/Final-{suffix}.otf"
    if not os.path.exists(path):
        print("skip (missing):", path); continue
    f = TTFont(path)
    name = f["name"]
    full = FAMILY if sub == "Regular" else f"{FAMILY} {sub}"
    ps = f"{FAMILY.replace(' ', '')}-{suffix}"
    # RIBBI: for Bold/Italic/Bold Italic keep them groupable under family=FAMILY.
    vals = {1: FAMILY, 2: sub, 3: f"{FAMILY} {sub}", 4: full, 6: ps, 16: FAMILY, 17: sub}
    for nid, val in vals.items():
        name.removeNames(nameID=nid)
        name.setName(val, nid, 3, 1, 0x409)  # Windows / Unicode BMP / en-US
        name.setName(val, nid, 1, 0, 0)       # Mac / Roman / en
    f.save(path)
    print(f"named {path}: family='{FAMILY}' sub='{sub}' ps='{ps}'")
