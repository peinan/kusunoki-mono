# /// script
# requires-python = ">=3.11"
# dependencies = ["fonttools>=4.50", "skia-pathops>=0.8"]
# ///
"""P2.8: enlarge kana dakuten (゛) / handakuten (゜) and skip-ink the overlap.

    KM_DAKUTEN_SCALE=1.3 KM_HANDAKUTEN_SCALE=1.25 KM_DAKUTEN_HALO=0.18 \\
        uv run scripts/enlarge_dakuten.py <lineseed.ttf> <out.ttf>

Each voiced kana X is rebuilt from its NFD parts as

    X' = (body ⊖ mark×SCALE×(1+HALO)) ∪ mark×SCALE      # skip-ink carve

where body / mark are recovered per glyph, most reliable method first:

1. Base diff: LINE Seed usually pastes the unvoiced base outline B unchanged
   (sometimes nudged 1–2 units — detected by matching contour bboxes), so
   mark = X ⊖ B and body = B. Works even when the mark is welded into a body
   contour (ぼ ブ …). A welded handakuten loses a chunk of its ring in X ⊖ B;
   those are rebuilt as concentric circles centred on the (never-welded) hole
   contour, sized like the clean siblings' rings.
2. Contour split: when the voiced body was redrawn (ヅ デ) or the diff turns to
   slivers (ゾ ダ グ ゴ), the mark is instead taken to be the small contours in
   the glyph's top-right; a dot welded into the body stays body there (partial
   enlarge). Glyphs failing both are left untouched and reported.

Everything runs in LINE Seed's own em, before P3 swaps the glyphs into the
base, so P3's scaling / centring / italic skew apply unchanged. Advances kept.

Env: KM_DAKUTEN_SCALE (dakuten enlarge factor, 1.3), KM_HANDAKUTEN_SCALE (ring
enlarge factor, 1.25), KM_DAKUTEN_HALO (carved gap as an extra fraction of the
enlarged mark, 0.18), KM_DAKUTEN_SKIP_INK (1=carve, 0=just enlarge),
KM_DAKUTEN_EXCLUDE (kana to leave untouched, default "ゞヾヷヸヹヺ").
"""
import os
import sys
import unicodedata

import pathops
from fontTools.misc.transform import Transform
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.recordingPen import DecomposingRecordingPen, RecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont

IN, OUT = sys.argv[1], sys.argv[2]
SCALE_DAKUTEN = float(os.environ.get("KM_DAKUTEN_SCALE", "1.3"))
SCALE_HANDAKUTEN = float(os.environ.get("KM_HANDAKUTEN_SCALE", "1.25"))
HALO = float(os.environ.get("KM_DAKUTEN_HALO", "0.18"))
SKIP_INK = os.environ.get("KM_DAKUTEN_SKIP_INK", "1") != "0"
EXCLUDE = set(os.environ.get("KM_DAKUTEN_EXCLUDE", "ゞヾヷヸヹヺ"))

VOICED, SEMI = "゙", "゚"   # combining marks NFD leaves behind
KAPPA = 0.5522847498307936    # cubic-Bézier circle constant
RESID_AREA = 3000             # units²/1000upm: bigger B ⊖ X residue = body was redrawn
SLIVER_AREA = 1000            # units²/1000upm: smaller mark contour = grid-fit noise
MAX_MARK = 0.45               # mark bbox must stay under this fraction of the em
MAX_PIECE = 0.30              # a mark contour is smaller than this fraction of the em


def targets(cmap):
    """In-font voiced / semi-voiced kana as (glyph, base_glyph, is_semi)."""
    out = []
    for cp in range(0x3040, 0x3100):
        ch = chr(cp)
        if ch in EXCLUDE:
            continue
        d = unicodedata.normalize("NFD", ch)
        if (len(d) == 2 and d[1] in (VOICED, SEMI)
                and 0x3040 <= ord(d[0]) < 0x3100      # base must be kana (not ゛゜ = space+mark)
                and cmap.get(cp) and cmap.get(ord(d[0]))):
            out.append((cmap[cp], cmap[ord(d[0])], d[1] == SEMI))
    return out


def split_value(rec_value):
    """A recording-pen value as [(contour_value, bbox), ...]."""
    groups, cur = [], []
    for cmd, args in rec_value:
        if cmd == "moveTo" and cur:
            groups.append(cur)
            cur = []
        cur.append((cmd, args))
    if cur:
        groups.append(cur)
    out = []
    for g in groups:
        bp = BoundsPen(None)
        r = RecordingPen()
        r.value = g
        r.replay(bp)
        if bp.bounds:
            out.append((g, bp.bounds))
    return out


def contours(gs, gname):
    """Glyph as [(contour_value, bbox), ...], components resolved."""
    rec = DecomposingRecordingPen(gs)
    gs[gname].draw(rec)
    return split_value(rec.value)


def path_contours(path):
    rec = RecordingPen()
    path.draw(rec)
    return split_value(rec.value)


def to_path(values):
    p = pathops.Path()
    r = RecordingPen()
    r.value = [cmd for v in values for cmd in v]
    r.replay(p.getPen())
    return p


def pbounds(path):
    bp = BoundsPen(None)
    path.draw(bp)
    return bp.bounds


def op(kind, a, b):
    out = pathops.Path()
    if kind == "union":                    # union(paths, outpen) — one operand list
        pathops.union([a, b], out.getPen())
    else:                                  # difference(subject, clip, outpen)
        getattr(pathops, kind)([a], [b], out.getPen())
    return out


def xform(path, t):
    out = pathops.Path()
    path.draw(TransformPen(out.getPen(), t))
    return out


def scaled_about(path, f, cx, cy):
    return xform(path, Transform().translate(cx, cy).scale(f).translate(-cx, -cy))


def circle(cx, cy, r):
    p = pathops.Path()
    pen = p.getPen()
    k = KAPPA * r
    pen.moveTo((cx + r, cy))
    pen.curveTo((cx + r, cy + k), (cx + k, cy + r), (cx, cy + r))
    pen.curveTo((cx - k, cy + r), (cx - r, cy + k), (cx - r, cy))
    pen.curveTo((cx - r, cy - k), (cx - k, cy - r), (cx, cy - r))
    pen.curveTo((cx + k, cy - r), (cx + r, cy - k), (cx + r, cy))
    pen.closePath()
    return p


def align_base(b_cts, x_cts):
    """The base pasted into X, re-nudged contour by contour.

    LINE Seed nudges each pasted contour independently (1–2 unit grid fits), so a
    single global offset leaves curved hairline residues. Match every B contour
    to the X contour with the same w×h (within 4 units) and translate it onto
    that contour; unmatched contours (welded ones) take the largest match's
    offset."""
    matched = []
    for v, b in b_cts:
        bw, bh = b[2] - b[0], b[3] - b[1]
        cand = min(x_cts, key=lambda xc: abs((xc[1][2] - xc[1][0]) - bw)
                   + abs((xc[1][3] - xc[1][1]) - bh))[1]
        mism = abs((cand[2] - cand[0]) - bw) + abs((cand[3] - cand[1]) - bh)
        off = (round(cand[0] - b[0]), round(cand[1] - b[1])) if mism <= 4 else None
        matched.append((v, b, off, bw * bh))
    fallback_off = max((m for m in matched if m[2]), key=lambda m: m[3], default=None)
    fallback_off = fallback_off[2] if fallback_off else (0, 0)
    p = pathops.Path()
    for v, _, off, _ in matched:
        dx, dy = off if off else fallback_off
        r = RecordingPen()
        r.value = v
        r.replay(TransformPen(p.getPen(), Transform().translate(dx, dy)))
    return p


def contour_area(value):
    """Approximate contour ink area (shoelace over on-curve + control points).
    Exactness doesn't matter: hairline grid-fit crescents measure in the hundreds
    of units², real strokes and mark dots in the many thousands."""
    pts = [p for cmd, args in value for p in (args if cmd != "closePath" else ())
           if p is not None]
    a = 0.0
    for i in range(len(pts)):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % len(pts)]
        a += x1 * y2 - x2 * y1
    return abs(a) / 2


def small_residue(path):
    """True if the B ⊖ X residue is only grid-fit noise, not a redrawn body."""
    scale2 = (upm / 1000) ** 2
    return sum(contour_area(v) for v, _ in path_contours(path)) <= RESID_AREA * scale2


def drop_slivers(path):
    """Strip hairline contours (grid-fit noise around body edges) from a mark."""
    scale2 = (upm / 1000) ** 2
    kept = [v for v, _ in path_contours(path) if contour_area(v) > SLIVER_AREA * scale2]
    return to_path(kept)


tt = TTFont(IN)
cmap = tt.getBestCmap()
gs = tt.getGlyphSet()
glyf = tt["glyf"]
hmtx = tt["hmtx"]
upm = tt["head"].unitsPerEm


def base_diff(xg, bg):
    """Method 1: mark = X ⊖ nudge-aligned B, body = B. None if residue/bounds say no."""
    x_cts, b_cts = contours(gs, xg), contours(gs, bg)
    X = to_path([v for v, _ in x_cts])
    B = align_base(b_cts, x_cts)
    if not small_residue(op("difference", B, X)):
        return "resid"                    # base sticks out of X: body was redrawn
    mark = drop_slivers(op("difference", X, B))
    mb = pbounds(mark)
    if not mb or (mb[2] - mb[0]) > MAX_MARK * upm or (mb[3] - mb[1]) > MAX_MARK * upm:
        return "mark-bounds"              # diff is body slivers, not a mark
    return mark, B, mb


def contour_split(xg, adv):
    """Method 2: mark = the small top-right contours of X, body = the rest."""
    cts = contours(gs, xg)
    ymin = min(b[1] for _, b in cts)
    ymax = max(b[3] for _, b in cts)
    mark_v, body_v = [], []
    for v, b in cts:
        w, h = b[2] - b[0], b[3] - b[1]
        cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
        if (w <= MAX_PIECE * upm and h <= MAX_PIECE * upm
                and cx >= 0.5 * adv and cy >= ymin + 0.55 * (ymax - ymin)):
            mark_v.append(v)
        else:
            body_v.append(v)
    if not mark_v or len(mark_v) > 3 or not body_v:
        return None
    mark = to_path(mark_v)
    return mark, to_path(body_v), pbounds(mark)


# Pass 1: recover mark + body per glyph; collect clean handakuten ring dimensions.
recovered, fell_back, skipped = {}, [], []
ring_dims = []                     # (w, h, hole_r) from clean rings, for weld repair
for gname, bname, is_semi in targets(cmap):
    got = base_diff(gname, bname)
    from_fallback = isinstance(got, str)
    if from_fallback:
        reason, got = got, contour_split(gname, hmtx[gname][0])
        if not got:
            skipped.append(f"{gname}({reason})")
            continue
        fell_back.append(f"{gname}({reason})")
    mark, body, mb = got
    recovered[gname] = (mark, body, is_semi, mb, from_fallback)
    if is_semi:
        w, h = mb[2] - mb[0], mb[3] - mb[1]
        if abs(w - h) < 0.05 * max(w, h):          # square bbox = intact ring
            holes = [b for _, b in contours(gs, gname)
                     if mb[0] < (b[0] + b[2]) / 2 < mb[2]
                     and mb[1] < (b[1] + b[3]) / 2 < mb[3]
                     and (b[2] - b[0]) < 0.8 * w]
            if holes:
                hb = min(holes, key=lambda b: b[2] - b[0])
                ring_dims.append((w, h, (hb[2] - hb[0] + hb[3] - hb[1]) / 4))

ring_dims.sort()
REF = ring_dims[len(ring_dims) // 2] if ring_dims else None

# Pass 2: repair welded rings, enlarge, carve, write back.
done, repaired = 0, []
for gname, (mark, body, is_semi, mb, from_fallback) in recovered.items():
    w, h = mb[2] - mb[0], mb[3] - mb[1]
    if is_semi and REF and (w < 0.95 * REF[0] or h < 0.95 * REF[1]):
        # ring welded into the body: the recovered mark lost a chunk. Rebuild it
        # as concentric circles centred on the hole contour (interior, so never
        # welded away), sized like the clean siblings' rings.
        holes = [b for _, b in contours(gs, gname)
                 if mb[0] - 0.3 * REF[0] < (b[0] + b[2]) / 2 < mb[2] + 0.3 * REF[0]
                 and mb[1] - 0.3 * REF[1] < (b[1] + b[3]) / 2 < mb[3] + 0.3 * REF[1]
                 and (b[2] - b[0]) < 0.8 * REF[0]]
        if not holes:
            skipped.append(f"{gname}(welded-no-hole)")
            continue
        hb = min(holes, key=lambda b: b[2] - b[0])
        cx, cy = (hb[0] + hb[2]) / 2, (hb[1] + hb[3]) / 2
        r_in = (hb[2] - hb[0] + hb[3] - hb[1]) / 4
        r_out = r_in * (REF[0] / 2) / REF[2]
        mark = op("difference", circle(cx, cy, r_out), circle(cx, cy, r_in))
        mb = pbounds(mark)
        if from_fallback:
            # the contour-split body still carries the welded old ring's ink,
            # which would sit inside the enlarged ring's hole — scrub the old
            # ring's disc out of the body before carving.
            body = op("difference", body, circle(cx, cy, r_out * 1.06))
        repaired.append(gname)

    scale = SCALE_HANDAKUTEN if is_semi else SCALE_DAKUTEN
    mcx, mcy = (mb[0] + mb[2]) / 2, (mb[1] + mb[3]) / 2
    mark_big = scaled_about(mark, scale, mcx, mcy)
    if SKIP_INK:
        halo = scaled_about(mark, scale * (1 + HALO), mcx, mcy)
        body = op("difference", body, halo)
    final = op("union", body, mark_big)

    adv = hmtx[gname][0]
    tt_pen = TTGlyphPen(gs)
    final.draw(Cu2QuPen(tt_pen, max_err=1.0))
    glyf[gname] = tt_pen.glyph()
    fb = pbounds(final)
    hmtx[gname] = (adv, int(round(fb[0])) if fb else 0)
    done += 1

tt.save(OUT)
msg = (f"[enlarge_dakuten] enlarged {done} kana "
       f"(dakuten={SCALE_DAKUTEN} handakuten={SCALE_HANDAKUTEN} "
       f"halo={HALO} skip_ink={int(SKIP_INK)}) -> {OUT}")
if repaired:
    msg += f"; rebuilt welded rings: {' '.join(repaired)}"
if fell_back:
    msg += f"; contour-split fallback: {' '.join(fell_back)}"
if skipped:
    msg += f"; SKIPPED {len(skipped)}: {' '.join(skipped)}"
print(msg)
