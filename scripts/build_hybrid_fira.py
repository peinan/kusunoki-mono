"""Build a "Fira Code skeleton + <source> ligature designs" font: for every Fira
Code ligature, flatten how the SOURCE font shapes that sequence and inject it into
Fira's ligature-glyph slot (outline only; keep Fira's advance + carrier
positioning). Ligaturizer then transplants THIS font's ligatures, so the result is
"<source> design, Fira logic". The source may be any ligature font with a `calt`
that fires on the bare sequences (JetBrains Mono, Iosevka, ...).

    uv run --with uharfbuzz --with fonttools python scripts/build_hybrid_fira.py SOURCE_TTF OUT.otf
"""
import sys, os
import uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools import agl
from fontTools.pens.recordingPen import DecomposingRecordingPen, RecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.qu2cuPen import Qu2CuPen
from fontTools.misc.transform import Transform

IOSE, OUTF = sys.argv[1], sys.argv[2]
LIGDIR = "build/ligaturizer"
FIRA = os.path.join(LIGDIR, "fonts/fira/distr/otf/FiraCode-Regular.otf")

sys.path.insert(0, LIGDIR)
import ligatures as ligmod
specs = [s for s in ligmod.ligatures if s.get("firacode_ligature_name")]

iose = TTFont(IOSE); iose_gs = iose.getGlyphSet(); iorder = iose.getGlyphOrder()
fira = TTFont(FIRA); fira_gs = fira.getGlyphSet(); fira_hmtx = fira["hmtx"]

def cap_h(font):
    gs = font.getGlyphSet(); bp = BoundsPen(gs); gs[font.getBestCmap()[ord("H")]].draw(bp)
    return bp.bounds[3] - bp.bounds[1]
S = cap_h(fira) / cap_h(iose)   # uniform Iosevka -> Fira scale (cap match)

blob = hb.Blob.from_file_path(IOSE); hbf = hb.Font(hb.Face(blob))

def text_of(chars):
    return "".join(agl.toUnicode(n) for n in chars)

def shape(text, on):
    buf = hb.Buffer(); buf.add_str(text); buf.guess_segment_properties()
    hb.shape(hbf, buf, {"calt": on, "liga": on})
    return [g.codepoint for g in buf.glyph_infos], buf.glyph_infos, buf.glyph_positions

def flatten(infos, pos):
    comb = RecordingPen(); penx = 0
    for info, p in zip(infos, pos):
        rec = DecomposingRecordingPen(iose_gs); iose_gs[iorder[info.codepoint]].draw(rec)
        rec.replay(TransformPen(comb, Transform().translate(penx + p.x_offset, p.y_offset)))
        penx += p.x_advance
    return comb

cff = fira["CFF "].cff; top = cff[cff.fontNames[0]]
inj, skip = 0, []
for spec in specs:
    name, chars = spec["firacode_ligature_name"], spec["chars"]
    if any(agl.toUnicode(n) == "" for n in chars): skip.append((name, "badname")); continue
    text = text_of(chars)
    on_ids, on_i, on_p = shape(text, True); off_ids, _, _ = shape(text, False)
    if on_ids == off_ids: skip.append((name, "no-source-ligature")); continue
    if name not in top.CharStrings: skip.append((name, "not-in-fira")); continue
    comb = flatten(on_i, on_p)
    bp = BoundsPen(None); comb.replay(bp)
    if not bp.bounds: skip.append((name, "empty-source")); continue
    ib = bp.bounds
    bpf = BoundsPen(fira_gs); fira_gs[name].draw(bpf)
    if not bpf.bounds: skip.append((name, "empty-fira")); continue
    fb = bpf.bounds; fadv = fira_hmtx[name][0]
    icx, icy = (ib[0] + ib[2]) / 2, (ib[1] + ib[3]) / 2
    fcx, fcy = (fb[0] + fb[2]) / 2, (fb[1] + fb[3]) / 2
    xform = Transform().translate(fcx - S * icx, fcy - S * icy).scale(S)
    t2 = T2CharStringPen(fadv, None)
    comb.replay(TransformPen(Qu2CuPen(t2, max_err=1.0, reverse_direction=True), xform))
    top.CharStrings[name] = t2.getCharString(private=top.Private, globalSubrs=top.GlobalSubrs)
    inj += 1
fira.save(OUTF)
print(f"scale={S:.4f}  injected={inj}  skipped={len(skip)}  -> {OUTF}")
for n, r in skip: print("  skip:", n, "-", r)
