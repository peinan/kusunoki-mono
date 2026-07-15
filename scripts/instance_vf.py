# /// script
# requires-python = ">=3.11"
# dependencies = ["fonttools>=4.50"]
# ///
"""Instance a variable font at a single weight -> static TTF.

    uv run scripts/instance_vf.py <vf.ttf> <out.ttf> <wght>
"""
import sys

from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

src, out, wght = sys.argv[1], sys.argv[2], float(sys.argv[3])
f = TTFont(src)
instancer.instantiateVariableFont(f, {"wght": wght}, inplace=True)
f.save(out)
print(f"[instance_vf] {out}  (wght={wght})")
