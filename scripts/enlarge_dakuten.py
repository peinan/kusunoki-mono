# /// script
# requires-python = ">=3.11"
# dependencies = ["fonttools>=4.50", "skia-pathops>=0.8"]
# ///
"""P2.8: enlarge kana dakuten (゛) / handakuten (゜) and skip-ink the overlap.

    KM_DAKUTEN_SCALE=1.3 KM_HANDAKUTEN_SCALE=1.25 KM_DAKUTEN_HALO=0.48 \\
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

A dakuten the recovery leaves broken — one dot welded into the body (グ ゴ ゾ
ダ ブ) or bitten by it (ぼ) — is rebuilt whole from the cleanest two-dot mark
of the same script, anchored on the intact top-right dot, so both dots always
move, scale, and carve together.

Per-character tuning: scripts/dakuten_overrides.json (or KM_DAKUTEN_OVERRIDES)
maps a kana to {"scale", "halo", "dx", "dy", "rot", "halo_pad", "skip_ink",
"exclude"} — values replace the global defaults for that kana. dx/dy move the
mark in font units, rot tilts it (degrees, CCW), halo_pad = [left, right, top,
bottom] widens the carved gap per side in font units, exclude leaves the glyph
untouched. Optional "bold" / "italic" / "bolditalic" sub-objects override those
base values per style (unset fields inherit). scripts/dakuten_tuner.py edits
the file visually. The stage runs once per style:

    uv run scripts/enlarge_dakuten.py <lineseed.ttf> <out.ttf> [style]

Everything runs in LINE Seed's own em, before P3 swaps the glyphs into the
base, so P3's scaling / centring / italic skew apply unchanged. Advances kept.

Env: KM_DAKUTEN_SCALE (dakuten enlarge factor, 1.3), KM_HANDAKUTEN_SCALE (ring
enlarge factor, 1.25), KM_DAKUTEN_HALO / KM_HANDAKUTEN_HALO (carved gap as an
extra fraction of the enlarged mark, 0.48 / 0.36), KM_DAKUTEN_SKIP_INK (1=carve,
0=just enlarge), KM_DAKUTEN_EXCLUDE (kana to leave untouched, "ゞヾヷヸヹヺ"),
KM_DAKUTEN_OVERRIDES (per-kana JSON, scripts/dakuten_overrides.json).
"""
import json
import math
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

SCALE_DAKUTEN = float(os.environ.get("KM_DAKUTEN_SCALE", "1.3"))
SCALE_HANDAKUTEN = float(os.environ.get("KM_HANDAKUTEN_SCALE", "1.25"))
HALO_DAKUTEN = float(os.environ.get("KM_DAKUTEN_HALO", "0.48"))
HALO_HANDAKUTEN = float(os.environ.get("KM_HANDAKUTEN_HALO", "0.36"))
SKIP_INK = os.environ.get("KM_DAKUTEN_SKIP_INK", "1") != "0"
EXCLUDE = set(os.environ.get("KM_DAKUTEN_EXCLUDE", "ゞヾヷヸヹヺ"))
OVERRIDES_PATH = os.environ.get(
    "KM_DAKUTEN_OVERRIDES",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "dakuten_overrides.json"))
STYLE_LAYERS = ("bold", "italic", "bolditalic")

VOICED, SEMI = "゙", "゚"   # combining marks NFD leaves behind
KAPPA = 0.5522847498307936    # cubic-Bézier circle constant
RESID_AREA = 3000             # units²/1000upm: bigger B ⊖ X residue = body was redrawn
SLIVER_AREA = 1000            # units²/1000upm: smaller mark contour = grid-fit noise
MAX_MARK = 0.45               # mark bbox must stay under this fraction of the em
MAX_PIECE = 0.30              # a mark contour is smaller than this fraction of the em


def default_scale(is_semi):
    return SCALE_HANDAKUTEN if is_semi else SCALE_DAKUTEN


def default_halo(is_semi):
    return HALO_HANDAKUTEN if is_semi else HALO_DAKUTEN


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


def load_overrides(path=None):
    path = path or OVERRIDES_PATH
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def resolve_override(entry, style):
    """Effective per-kana settings for a style: base fields, then the style's
    own layer on top (Regular = base only; unset fields inherit)."""
    out = {k: v for k, v in (entry or {}).items() if k not in STYLE_LAYERS}
    key = style.lower()
    if key in STYLE_LAYERS:
        out.update((entry or {}).get(key, {}))
    return out


class DakutenFont:
    """A LINE Seed weight with its voiced kana recovered into body + mark."""

    def __init__(self, path):
        self.tt = TTFont(path)
        self.cmap = self.tt.getBestCmap()
        self.gs = self.tt.getGlyphSet()
        self.glyf = self.tt["glyf"]
        self.hmtx = self.tt["hmtx"]
        self.upm = self.tt["head"].unitsPerEm

    def targets(self):
        """In-font voiced / semi-voiced kana as (char, glyph, base_glyph, is_semi)."""
        out = []
        for cp in range(0x3040, 0x3100):
            ch = chr(cp)
            if ch in EXCLUDE:
                continue
            d = unicodedata.normalize("NFD", ch)
            if (len(d) == 2 and d[1] in (VOICED, SEMI)
                    and 0x3040 <= ord(d[0]) < 0x3100   # base must be kana (not ゛゜)
                    and self.cmap.get(cp) and self.cmap.get(ord(d[0]))):
                out.append((ch, self.cmap[cp], self.cmap[ord(d[0])], d[1] == SEMI))
        return out

    def contours(self, gname):
        """Glyph as [(contour_value, bbox), ...], components resolved."""
        rec = DecomposingRecordingPen(self.gs)
        self.gs[gname].draw(rec)
        return split_value(rec.value)

    def _small_residue(self, path):
        """True if the B ⊖ X residue is only grid-fit noise, not a redrawn body."""
        scale2 = (self.upm / 1000) ** 2
        return sum(contour_area(v) for v, _ in path_contours(path)) <= RESID_AREA * scale2

    def _drop_slivers(self, path):
        """Strip hairline contours (grid-fit noise around body edges) from a mark."""
        scale2 = (self.upm / 1000) ** 2
        kept = [v for v, _ in path_contours(path)
                if contour_area(v) > SLIVER_AREA * scale2]
        return to_path(kept)

    def _base_diff(self, xg, bg):
        """Method 1: mark = X ⊖ nudge-aligned B, body = B. Reason string if not."""
        x_cts, b_cts = self.contours(xg), self.contours(bg)
        X = to_path([v for v, _ in x_cts])
        B = align_base(b_cts, x_cts)
        if not self._small_residue(op("difference", B, X)):
            return "resid"                # base sticks out of X: body was redrawn
        mark = self._drop_slivers(op("difference", X, B))
        mb = pbounds(mark)
        if not mb or (mb[2] - mb[0]) > MAX_MARK * self.upm or (mb[3] - mb[1]) > MAX_MARK * self.upm:
            return "mark-bounds"          # diff is body slivers, not a mark
        return mark, B, mb

    def _contour_split(self, xg, adv):
        """Method 2: mark = the small top-right contours of X, body = the rest."""
        cts = self.contours(xg)
        ymin = min(b[1] for _, b in cts)
        ymax = max(b[3] for _, b in cts)
        mark_v, body_v = [], []
        for v, b in cts:
            w, h = b[2] - b[0], b[3] - b[1]
            cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
            if (w <= MAX_PIECE * self.upm and h <= MAX_PIECE * self.upm
                    and cx >= 0.5 * adv and cy >= ymin + 0.55 * (ymax - ymin)):
                mark_v.append(v)
            else:
                body_v.append(v)
        if not mark_v or len(mark_v) > 3 or not body_v:
            return None
        mark = to_path(mark_v)
        return mark, to_path(body_v), pbounds(mark)

    def recover(self):
        """Recover body + mark for every voiced kana; repair welded rings.

        Returns (kana, fell_back, skipped, repaired, rebuilt) where kana maps
        char -> {gname, mark, body, mb, is_semi, fallback}. Repairs are
        geometry fixes independent of the tuning parameters, so they live
        here, not in compose()."""
        kana, fell_back, skipped = {}, [], []
        ring_dims = []                 # (w, h, hole_r) from clean rings, for repair
        for ch, gname, bname, is_semi in self.targets():
            got = self._base_diff(gname, bname)
            from_fallback = isinstance(got, str)
            if from_fallback:
                reason, got = got, self._contour_split(gname, self.hmtx[gname][0])
                if not got:
                    skipped.append(f"{gname}({reason})")
                    continue
                fell_back.append(f"{gname}({reason})")
            mark, body, mb = got
            kana[ch] = {"gname": gname, "mark": mark, "body": body, "mb": mb,
                        "is_semi": is_semi, "fallback": from_fallback}
            if is_semi:
                w, h = mb[2] - mb[0], mb[3] - mb[1]
                if abs(w - h) < 0.05 * max(w, h):      # square bbox = intact ring
                    holes = [b for _, b in self.contours(gname)
                             if mb[0] < (b[0] + b[2]) / 2 < mb[2]
                             and mb[1] < (b[1] + b[3]) / 2 < mb[3]
                             and (b[2] - b[0]) < 0.8 * w]
                    if holes:
                        hb = min(holes, key=lambda b: b[2] - b[0])
                        ring_dims.append((w, h, (hb[2] - hb[0] + hb[3] - hb[1]) / 4))

        ring_dims.sort()
        ref = ring_dims[len(ring_dims) // 2] if ring_dims else None

        repaired = []
        for ch, d in list(kana.items()):
            mb = d["mb"]
            w, h = mb[2] - mb[0], mb[3] - mb[1]
            if not (d["is_semi"] and ref and (w < 0.95 * ref[0] or h < 0.95 * ref[1])):
                continue
            # ring welded into the body: the recovered mark lost a chunk. Rebuild
            # it as concentric circles centred on the hole contour (interior, so
            # never welded away), sized like the clean siblings' rings.
            holes = [b for _, b in self.contours(d["gname"])
                     if mb[0] - 0.3 * ref[0] < (b[0] + b[2]) / 2 < mb[2] + 0.3 * ref[0]
                     and mb[1] - 0.3 * ref[1] < (b[1] + b[3]) / 2 < mb[3] + 0.3 * ref[1]
                     and (b[2] - b[0]) < 0.8 * ref[0]]
            if not holes:
                skipped.append(f"{d['gname']}(welded-no-hole)")
                del kana[ch]
                continue
            hb = min(holes, key=lambda b: b[2] - b[0])
            cx, cy = (hb[0] + hb[2]) / 2, (hb[1] + hb[3]) / 2
            r_in = (hb[2] - hb[0] + hb[3] - hb[1]) / 4
            r_out = r_in * (ref[0] / 2) / ref[2]
            d["mark"] = op("difference", circle(cx, cy, r_out), circle(cx, cy, r_in))
            d["mb"] = pbounds(d["mark"])
            if d["fallback"]:
                # the contour-split body still carries the welded old ring's ink,
                # which would sit inside the enlarged ring's hole — scrub the old
                # ring's disc out of the body before carving.
                d["body"] = op("difference", d["body"], circle(cx, cy, r_out * 1.06))
            repaired.append(d["gname"])

        rebuilt = self._rebuild_broken_dakuten(kana)
        return kana, fell_back, skipped, repaired, rebuilt

    def _rebuild_broken_dakuten(self, kana):
        """Replace broken dakuten with the cleanest same-script two-dot mark.

        A dakuten can come out of recovery with only one dot (the other welded
        into a body contour: グ ゴ ゾ ダ ブ) or with a dot bitten by the weld
        (ぼ) — those can't move or carve as a pair. Anchor the template on the
        intact top-right dot and drop it in; for contour-split bodies also
        scrub the welded dot's leftover ink."""
        top_right = lambda cts: max((b for _, b in cts), key=lambda b: b[0] + b[2] + b[1] + b[3])
        center = lambda b: ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)
        script = lambda ch: "hira" if ord(ch) < 0x30A0 else "kata"

        templates = {}
        for ch, d in kana.items():
            if d["is_semi"] or d["fallback"]:
                continue
            cts = path_contours(d["mark"])
            if len(cts) != 2:
                continue
            areas = sorted(contour_area(v) for v, _ in cts)
            ratio = areas[0] / areas[1]
            if ratio >= 0.85 and (script(ch) not in templates or ratio > templates[script(ch)][0]):
                templates[script(ch)] = (ratio, d["mark"])

        rebuilt = []
        for ch, d in kana.items():
            if d["is_semi"] or script(ch) not in templates:
                continue
            tmark = templates[script(ch)][1]
            tb = pbounds(tmark)
            cts = path_contours(d["mark"])
            areas = [contour_area(v) for v, _ in cts]
            broken = (
                (len(cts) == 1 and (d["mb"][2] - d["mb"][0]) < 0.75 * (tb[2] - tb[0]))
                or (len(cts) == 2 and min(areas) / max(areas) < 0.7)
                or len(cts) > 2)
            if not broken:
                continue
            fx, fy = center(top_right(cts))
            tx, ty = center(top_right(path_contours(tmark)))
            d["mark"] = xform(tmark, Transform().translate(round(fx - tx), round(fy - ty)))
            d["mb"] = pbounds(d["mark"])
            if d["fallback"]:
                # the welded dot's ink is still part of the body — scrub around
                # the rebuilt mark (the intact dot's region holds no body ink,
                # so only the weld leftovers go)
                mcx, mcy = center(d["mb"])
                d["body"] = op("difference", d["body"],
                               scaled_about(d["mark"], 1.12, mcx, mcy))
            rebuilt.append(d["gname"])
        return rebuilt

    @staticmethod
    def compose(d, scale, halo_frac, skip_ink, dx=0, dy=0, rot=0, pads=(0, 0, 0, 0)):
        """The tuned glyph: enlarged / moved / tilted mark on the carved body.

        pads = [left, right, top, bottom] widen the carved halo per side, in
        font units, applied to the un-rotated halo whose bbox is analytically
        mb×K — the tuner's SVG preview repeats the same closed-form transforms,
        so both always agree. Rotation comes last, about the mark centre."""
        mark, body, mb = d["mark"], d["body"], d["mb"]
        if dx or dy:
            mark = xform(mark, Transform().translate(dx, dy))
        mcx, mcy = (mb[0] + mb[2]) / 2 + dx, (mb[1] + mb[3]) / 2 + dy
        mark_big = scaled_about(mark, scale, mcx, mcy)
        halo = None
        if skip_ink:
            K = scale * (1 + halo_frac)
            halo = scaled_about(mark, K, mcx, mcy)
            l, r, t, b = pads
            if l or r or t or b:
                w, h = (mb[2] - mb[0]) * K, (mb[3] - mb[1]) * K
                halo = xform(halo, Transform()
                             .translate(mcx + (r - l) / 2, mcy + (t - b) / 2)
                             .scale((w + l + r) / w, (h + t + b) / h)
                             .translate(-mcx, -mcy))
        if rot:
            spin = (Transform().translate(mcx, mcy)
                    .rotate(math.radians(rot)).translate(-mcx, -mcy))
            mark_big = xform(mark_big, spin)
            halo = xform(halo, spin) if halo is not None else None
        if halo is not None:
            body = op("difference", body, halo)
        return op("union", body, mark_big)

    def write_glyph(self, gname, final):
        adv = self.hmtx[gname][0]
        tt_pen = TTGlyphPen(self.gs)
        final.draw(Cu2QuPen(tt_pen, max_err=1.0))
        self.glyf[gname] = tt_pen.glyph()
        fb = pbounds(final)
        self.hmtx[gname] = (adv, int(round(fb[0])) if fb else 0)


def main():
    src, out = sys.argv[1], sys.argv[2]
    style = sys.argv[3] if len(sys.argv) > 3 else "Regular"
    font = DakutenFont(src)
    kana, fell_back, skipped, repaired, rebuilt = font.recover()
    overrides = load_overrides()

    done, tuned, excluded = 0, 0, []
    for ch, d in kana.items():
        o = resolve_override(overrides.get(ch), style)
        if o.get("exclude"):
            excluded.append(ch)
            continue
        if o:
            tuned += 1
        final = font.compose(
            d,
            o.get("scale", default_scale(d["is_semi"])),
            o.get("halo", default_halo(d["is_semi"])),
            o.get("skip_ink", SKIP_INK),
            o.get("dx", 0), o.get("dy", 0),
            o.get("rot", 0), o.get("halo_pad", (0, 0, 0, 0)),
        )
        font.write_glyph(d["gname"], final)
        done += 1

    font.tt.save(out)
    msg = (f"[enlarge_dakuten] {style}: enlarged {done} kana "
           f"(dakuten={SCALE_DAKUTEN} handakuten={SCALE_HANDAKUTEN} "
           f"halo={HALO_DAKUTEN}/{HALO_HANDAKUTEN} skip_ink={int(SKIP_INK)}) -> {out}")
    if tuned or excluded:
        msg += f"; overrides: {tuned} tuned, {len(excluded)} excluded ({OVERRIDES_PATH})"
    if repaired:
        msg += f"; rebuilt welded rings: {' '.join(repaired)}"
    if rebuilt:
        msg += f"; rebuilt broken dakuten: {' '.join(rebuilt)}"
    if fell_back:
        msg += f"; contour-split fallback: {' '.join(fell_back)}"
    if skipped:
        msg += f"; SKIPPED {len(skipped)}: {' '.join(skipped)}"
    print(msg)


if __name__ == "__main__":
    main()
