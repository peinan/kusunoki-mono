# /// script
# requires-python = ">=3.10"
# dependencies = ["fonttools>=4.50", "brotli>=1.1"]
# ///
"""Verify the built fonts and emit a self-contained specimen HTML.

    uv run specimen.py

For every dist/KusunokiMono-<style>.ttf this runs metric assertions (advances,
isFixedPitch, CP932, ligature GSUB, glyph limits) and, unless any fail, writes
dist/specimen.html with the four styles embedded (WOFF2) so the result can be
eyeballed in a browser: alignment, ligatures, CJK, Nerd icons, box drawing.
"""
import base64
import io
import os
import sys

from fontTools.ttLib import TTFont

DIST = os.environ.get("DIST_DIR", "dist")
FAMILY = os.environ.get("FAMILY", "Kusunoki Mono")
VERSION = os.environ.get("VERSION", "0.0.0")
WIDTH_EM = float(os.environ.get("WIDTH_EM", "0.6"))
TARGET_EM = int(os.environ.get("TARGET_EM", "1000"))
HALF = round(WIDTH_EM * TARGET_EM)
FULL = 2 * HALF

STYLES = ["Regular", "Bold", "Italic", "BoldItalic"]
GREEN, RED, DIM, RST = "\033[32m", "\033[31m", "\033[2m", "\033[0m"


def best_cmap(font):
    return font.getBestCmap()


def advance(font, cmap, cp):
    gn = cmap.get(cp)
    return font["hmtx"][gn][0] if gn else None


def gsub_features(font):
    g = font.get("GSUB")
    if not g:
        return set()
    return {fr.FeatureTag for fr in g.table.FeatureList.FeatureRecord}


def verify(style):
    """Return (ok, rows) where rows is a list of (name, ok, detail)."""
    path = os.path.join(DIST, f"KusunokiMono-{style}.ttf")
    if not os.path.exists(path):
        return False, [("file exists", False, path)]
    f = TTFont(path)
    cmap = best_cmap(f)
    rows = []

    def row(name, ok, detail):
        rows.append((name, ok, str(detail)))

    ng = f["maxp"].numGlyphs
    row("glyphs <= 65535", ng <= 65535, ng)
    row("unitsPerEm == %d" % TARGET_EM, f["head"].unitsPerEm == TARGET_EM, f["head"].unitsPerEm)
    row("isFixedPitch", f["post"].isFixedPitch == 1, f["post"].isFixedPitch)
    row("OS/2 CP932 bit", bool(f["OS/2"].ulCodePageRange1 & (1 << 17)), True)

    for label, cp in [("'0'", 0x30), ("'A'", 0x41), ("'@'", 0x40)]:
        a = advance(f, cmap, cp)
        row(f"half-width {label} == {HALF}", a == HALF, a)
    for label, cp in [("'あ'", 0x3042), ("'一'", 0x4E00), ("U+3000", 0x3000)]:
        a = advance(f, cmap, cp)
        row(f"full-width {label} == {FULL}", a == FULL, a)

    feats = gsub_features(f)
    row("ligatures (calt)", "calt" in feats, "calt" in feats)

    for label, cp in [("kanji 日", 0x65E5), ("kana ア", 0x30A2), ("nerd ", 0xE0B0)]:
        row(f"has {label}", cp in cmap, cp in cmap)

    if "Italic" in style:
        row("italic angle set", f["post"].italicAngle != 0, f["post"].italicAngle)
        row("OS/2 italic bit", bool(f["OS/2"].fsSelection & 1), True)
    if "Bold" in style:
        row("weight 700", f["OS/2"].usWeightClass == 700, f["OS/2"].usWeightClass)

    f.close()
    ok = all(r[1] for r in rows)
    return ok, rows


def woff2_b64(path):
    f = TTFont(path)
    f.flavor = "woff2"
    buf = io.BytesIO()
    f.save(buf)
    f.close()
    return base64.b64encode(buf.getvalue()).decode("ascii")


CODE_SAMPLE = """\
// Kusunoki Mono — ligature & operator test
const clamp = (x, lo, hi) => x <= lo ? lo : x >= hi ? hi : x;
let ok = a == b && c != d || e === f;   // == != === !==
pipe |> map |> filter |> reduce;        // |>  <|
arrow: -> <- => <= >= <-> <=> ==> --> ;
misc:  /* */ // /// ::= ... .. www </> <!-- --> ++ -- **
0O0 1lI  #[0x1F] flags -Wall --verbose  0xDEAD_BEEF"""

JP_SAMPLE = """\
いろはにほへと ちりぬるを わかよたれそ つねならむ
和文と欧文 (Latin) の混植 mixed テスト 123 — 全角／半角。
プログラミング用等幅フォント「Kusunoki Mono」楠。日本語表示テスト。"""

ALIGN_SAMPLE = """\
|--------|--------|   half cells vs full cells
|ABCDEFGH|IJKLMNOP|   8 half-width columns
|あいうえ|かきくけ|   4 full-width = 8 half-width
|漢字表示|テスト枠|   should line up with the ru: above"""

NERD_SAMPLE = "               "
BOX_SAMPLE = "┌───┬───┐\n│ a │ b │\n├───┼───┤\n│ c │ d │\n└───┴───┘   ║╔═╗║ ╭──╮ ▏▎▍▌▋▊▉█ ░▒▓"


def build_html(results):
    faces = []
    fam = {"Regular": (400, "normal"), "Bold": (700, "normal"),
           "Italic": (400, "italic"), "BoldItalic": (700, "italic")}
    for style in STYLES:
        path = os.path.join(DIST, f"KusunokiMono-{style}.ttf")
        if not os.path.exists(path):
            continue
        weight, slant = fam[style]
        b64 = woff2_b64(path)
        faces.append(
            "@font-face{font-family:'Kusunoki Mono';font-weight:%d;font-style:%s;"
            "src:url(data:font/woff2;base64,%s) format('woff2');}" % (weight, slant, b64)
        )

    # metric table
    trows = []
    for style, (ok, rows) in results.items():
        badge = "PASS" if ok else "FAIL"
        cls = "ok" if ok else "bad"
        details = " · ".join(f"{'✓' if r[1] else '✗'} {r[0]}" for r in rows if not r[1]) or "all checks passed"
        trows.append(f"<tr class='{cls}'><td>{style}</td><td>{badge}</td><td>{details}</td></tr>")
    table = "<table class='metrics'><tr><th>style</th><th>result</th><th>notes</th></tr>" + "".join(trows) + "</table>"

    def esc(s):
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def block(title, content, style_css=""):
        return f"<section><h2>{esc(title)}</h2><pre style='{style_css}'>{esc(content)}</pre></section>"

    body = [
        f"<header><h1>{FAMILY}</h1><p>v{VERSION} · width {WIDTH_EM}em (half={HALF}, full={FULL}) · Iosevka + BIZ UDGothic + Nerd Fonts</p></header>",
        f"<section><h2>Metric verification</h2>{table}</section>",
        block("Alignment (full-width must equal 2 half-width)", ALIGN_SAMPLE),
        block("Ligatures & operators — Regular", CODE_SAMPLE),
        block("Ligatures & operators — Bold", CODE_SAMPLE, "font-weight:700"),
        block("Ligatures & operators — Italic", CODE_SAMPLE, "font-style:italic"),
        block("Japanese & mixed", JP_SAMPLE),
        block("Japanese — Bold", JP_SAMPLE, "font-weight:700"),
        block("Nerd Fonts icons", NERD_SAMPLE),
        block("Box drawing & blocks", BOX_SAMPLE),
        "<section><h2>Ideographic space U+3000</h2><pre>[　　] two visualized full-width spaces between the brackets</pre></section>",
        "<section><h2>Sizes</h2>" + "".join(
            f"<pre style='font-size:{sz}px'>Kusunoki 楠 Mono =&gt; 日本語 {sz}px</pre>" for sz in (12, 14, 16, 20, 28)
        ) + "</section>",
    ]

    css = """
:root{color-scheme:light dark}
*{box-sizing:border-box}
body{margin:0;padding:2rem;max-width:1000px;margin-inline:auto;
  font-family:system-ui,sans-serif;line-height:1.5;color:#1a1a1a;background:#fafafa}
header h1{font-family:'Kusunoki Mono',monospace;font-size:2.4rem;margin:0}
header p{color:#666;margin:.3rem 0 0}
section{margin:2rem 0}
h2{font-size:.95rem;text-transform:uppercase;letter-spacing:.05em;color:#888;
  border-bottom:1px solid #ddd;padding-bottom:.3rem}
pre{font-family:'Kusunoki Mono',monospace;font-size:16px;font-feature-settings:'calt' 1;
  background:#fff;border:1px solid #e3e3e3;border-radius:8px;padding:1rem;overflow-x:auto;white-space:pre}
table.metrics{width:100%;border-collapse:collapse;font-size:.9rem}
table.metrics td,table.metrics th{border:1px solid #e3e3e3;padding:.4rem .6rem;text-align:left}
tr.ok td:nth-child(2){color:#0a7f3f;font-weight:700}
tr.bad td:nth-child(2){color:#c0392b;font-weight:700}
@media (prefers-color-scheme:dark){
  body{background:#161616;color:#e8e8e8}
  header p,h2{color:#999}
  pre{background:#1e1e1e;border-color:#333}
  table.metrics td,table.metrics th{border-color:#333}
}
"""
    return ("<!doctype html><html><head><meta charset='utf-8'>"
            f"<title>{FAMILY} specimen</title><style>{css}{''.join(faces)}</style></head>"
            f"<body>{''.join(body)}</body></html>")


def main():
    print(f"{DIM}== {FAMILY} verification =={RST}")
    results = {}
    all_ok = True
    for style in STYLES:
        ok, rows = verify(style)
        results[style] = (ok, rows)
        all_ok &= ok
        badge = f"{GREEN}PASS{RST}" if ok else f"{RED}FAIL{RST}"
        print(f"  {style:12s} {badge}")
        for name, rok, detail in rows:
            if not rok:
                print(f"      {RED}✗ {name}{RST}  (got {detail})")

    html = build_html(results)
    out = os.path.join(DIST, "specimen.html")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(html)
    print(f"{DIM}specimen -> {out}{RST}")
    if not all_ok:
        print(f"{RED}Some metric checks FAILED.{RST}")
        sys.exit(1)
    print(f"{GREEN}All metric checks passed.{RST}")


if __name__ == "__main__":
    main()
