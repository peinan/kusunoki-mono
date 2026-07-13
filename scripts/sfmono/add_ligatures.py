"""Add JetBrains Mono's programming ligatures to the font, scaled to fit.

    fontforge -quiet -script scripts/sfmono/add_ligatures.py <target.otf> <jetbrains.ttf> <out.otf>

JetBrains uses a terminal-safe spacer `calt`: for a sequence the leading cells
become a blank SPC and the last cell holds a wide `.liga` glyph. We copy those
glyphs, scaled NON-uniformly — horizontally by the cell ratio (so a ligature
still spans N cells) and vertically to the target's x-height (so tall operators
like `/` aren't oversized, issue #7) — then import JetBrains's calt lookups.

Env: LIG_YSCALE overrides the vertical scale (default = x-height match; lower it,
e.g. toward the `/` match, if ligatures still read too tall).
"""
import math
import os
import shutil
import sys

import fontforge
import psMat


TARGET, JBPATH, OUT = sys.argv[1:4]


def ink_h(font, ch):
    b = font[ord(ch)].boundingBox()
    return b[3] - b[1]


t = fontforge.open(TARGET)
jb = fontforge.open(JBPATH)

sx = float(t["H"].width) / float(jb["H"].width)          # cell ratio (1024/600)
sy = float(os.environ.get("LIG_YSCALE", "0")) or (ink_h(t, "x") / ink_h(jb, "x"))
# Slant the ligatures to match an italic target (its own italic angle).
rad = math.radians(-t.italicangle) if abs(t.italicangle) > 0.1 else 0.0
print(f"[add_ligatures] sx={sx:.4f} sy={sy:.4f} italic={t.italicangle:.1f}deg")

lig = [g.glyphname for g in jb.glyphs()
       if g.glyphname == "SPC" or g.glyphname.endswith(".liga")]
print(f"[add_ligatures] ligature glyphs: {len(lig)}")

# Scale the ligature/spacer glyphs in a throwaway copy and merge them in.
# (Open a file COPY — fontforge.open() returns the same object for the same
# path, so opening JBPATH again would alias `jb` and closing it would close jb.)
jbsrc = OUT + ".jbsrc.ttf"
shutil.copy(JBPATH, jbsrc)
jb2 = fontforge.open(jbsrc)
keep = set(lig)
for g in list(jb2.glyphs()):
    if g.glyphname not in keep:
        try:
            jb2.removeGlyph(g.glyphname)
        except Exception:
            pass
for name in lig:
    g = jb2[name]
    w = g.width
    g.transform(psMat.scale(sx, sy))
    if rad:
        g.transform(psMat.skew(rad))
    g.width = round(w * sx)
tmp = OUT + ".lig.ttf"
jb2.generate(tmp)
jb2.close()
os.remove(jbsrc)
t.mergeFonts(tmp)
os.remove(tmp)

# Import JetBrains's calt lookups (by name) into the target.
calt = [nm for nm in jb.gsub_lookups
        if any(f[0] == "calt" for f in jb.getLookupInfo(nm)[2])]
print(f"[add_ligatures] calt lookups: {len(calt)}")
for nm in calt:
    try:
        t.importLookups(jb, nm)
    except Exception as e:
        print(f"  import fail {nm}: {e}")
jb.close()

t.generate(OUT)
t.close()
print(f"[add_ligatures] -> {OUT}")
