#!/usr/bin/env fontforge
"""Thicken only the Iosevka italic letters that the combined font takes from
Iosevka (q, s), so their stems match SFMS after grafting. Operates on the
throwaway Iosevka *source*; the SFMS CFF is untouched by FontForge.

    fontforge -quiet -script scripts/poc_thicken_iosevka.py <amount>
"""
import sys, fontforge

AMOUNT = float(sys.argv[1]) if len(sys.argv) > 1 else 8.0
SRC = "dist-0.5em/KusunokiMonoNFLG/KusunokiMonoNFLG-Italic.ttf"
OUT = "build/poc/_ios-italic-thick.ttf"
LETTERS = "qs"

f = fontforge.open(SRC)
cmap = {g.unicode: g.glyphname for g in f.glyphs() if g.unicode in [ord(c) for c in LETTERS]}
for c in LETTERS:
    g = f[cmap[ord(c)]]
    g.changeWeight(AMOUNT, "auto")
    g.removeOverlap()          # clean up any self-intersections from thickening
    g.correctDirection()
    g.round()
f.generate(OUT)
print(f"thickened {LETTERS} by {AMOUNT} -> {OUT}")
