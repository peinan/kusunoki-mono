<div align="center">

English | [日本語](development.ja.md)

</div>

# Development notes

How the build works and why, for changing the pipeline. To just build and
install the font, see the [README](../README.md).

## Layout

- `scripts/` — the whole pipeline: `setup.sh` fetches sources, `build.sh`
  runs the phases below; one Python script per transform.
- `sources/` — fetched inputs (gitignored; versions pinned in `setup.sh`).
- `build/sfms/` — per-phase intermediates and logs; the final four OTFs land
  in `build/sfms/dist/` (all gitignored).

FontForge scripts run via `fontforge -script`; the fontTools ones declare
inline dependencies (PEP 723) and run via `uv run`, so there is no venv to
set up. Each script's docstring is its usage reference.

## Pipeline

`build.sh` builds Regular → Bold → Italic → BoldItalic, roughly 2 minutes
per style; each phase logs to `build/sfms/<style>.p<n>.log`.

### P1 — base (`build_base.py`)

SF Mono is condensed uniformly ×0.809 (= 1024/1266) onto a square grid:
Latin advance 1024 at EM 2048, so a full-width CJK glyph (2048) is exactly
two columns. Migu 1M supplies kana, kanji, and CJK punctuation (em
1000→2048, ×`JP_SCALE` 0.82, centred; half-width katakana in the half
cell), plus the symbols SF Mono lacks (※, arrows, ★ …). Those filled
symbols take their advance from Unicode East Asian Width, because terminals
count cells from EAW, not from the font; `KM_AMBIGUOUS_WIDTH` decides the
ambiguous ones (※ ★ ℃). U+3000 becomes visible as the intersection of
☐ (U+2610) and ✚ (U+271A) — the Ricty idea that SF Mono Square also uses.
Italic styles skew the JP to SF Mono's italic angle.

### P2 — Nerd icons (official `font-patcher`)

The pinned v3.4.0 patcher runs with
`--complete --variable-width-glyphs --careful`: this "Propo" mode keeps each
icon's natural width and per-set size, like SF Mono Square.
`--single-width-glyphs` would pack every icon into one half cell and shrink
non-Powerline icons to ~50% height (issue #9). Existing Latin/CJK advances
are untouched either way.

### P2.5 — icon downscale (`plan_icon_scale.py` + `apply_icon_scale.py`)

nerd-fonts v3.4.0 draws some icons taller than the older set embedded in SF
Mono Square, so icons taller than a local SFMS reference (`KM_SFMS_DIR`,
default `~/Library/Fonts`) are shrunk to its height. Only glyphs that are
the *same drawing* in both fonts are touched (rasterize, crop to ink,
normalize, mask IoU ≥ 0.6) — icon sets drift between versions, and resizing
a different drawing to another's size is meaningless. Powerline, box
drawing, and braille are excluded because they must fill the cell. The plan
is computed once from Regular into `build/sfms/iconscale.json` and reused
for every style; each glyph scales about its ink centre with the advance
kept. The phase is skipped when no SFMS reference exists, and nothing
SFMS-derived is committed.

### P2.6 — ligatures (`instance_vf.py` + `add_ligatures.py`)

JetBrains Mono (instanced at wght 400/700) provides the programming
ligatures. Its `calt` is terminal-safe: the leading cells of a sequence
become blank spacers and the last cell holds one wide `.liga` glyph, so a
ligature still occupies N columns. The glyphs are copied with a non-uniform
scale — horizontally by the cell ratio (1024/600), vertically by
`LIG_YSCALE`: the script's default is an x-height match, and the build pins
`1.478`, tuned so tall operators like `//` match SF Mono's `/` (issue #7).
Italic styles slant the ligatures to the font's angle.

### P3 — Japanese swap (`swap_lineseed.py`)

Kana, katakana, kanji, and CJK punctuation present in both the base and
LINE Seed JP are replaced; everything else (SF Mono Latin, icons, the rare
kanji LINE Seed lacks) stays Migu. Each glyph is scaled to the base's CJK
size (measured on 国永日) and centred in the full-width cell, advance kept.
Two exceptions keep LINE Seed's own horizontal placement instead of being
centred (issue #4): 、。 and the full-width brackets — their left side
bearing maps proportionally into the cell, so open brackets hug the right
and close brackets hug the left.

### P4 — italic graft (`graft_italic.py` + `center_italic.py`; italic styles)

14 lowercase letters (a b c d e f i j k l p v y z) come from Google Sans
Code's true italic, instanced thinner than the target weight
(`GSC_R`/`GSC_B`) to match SF Mono's stems, x-height-matched, and placed at
the median ink-centre offset of the SF Mono letters that stay.
`center_italic.py` then shifts the ASCII uniformly so the median ink offset
equals `ITALIC_INK_OFFSET` × cell (0 = centred like the upright; SF Mono's
native lean is +7.6%).

### P5 — finalize (`finalize.py`)

RIBBI name table under the single family "Kusunoki Mono", vertical metrics
1638/-410 at 2048 UPM (= SF Mono Square), PANOSE monospace, Latin + Japanese
code pages, and a copyright/license note recording that the font embeds SF
Mono and must not be redistributed. `KM_VERSION` sets the version string.

## Sources and pinning (`setup.sh`)

Idempotent — re-running skips anything already present. macOS-only (Apple's
DMG is extracted with hdiutil/pkgutil):

- **SF Mono** — Apple's official `SF-Mono.dmg` (design-resources CDN)
- **Migu 1M** — the v2020.0307 release zip
- **nerd-fonts FontPatcher** — v3.4.0
- **LINE Seed JP / Google Sans Code / JetBrains Mono** — google/fonts `main` (OFL)

## Metrics cheat sheet

- EM 2048; Latin advance 1024 = SF Mono's 1266 × 0.809; CJK advance 2048.
- Ascent/descent 1638/-410 (baseline-to-baseline = 2048), set before the
  Nerd patch.
- Japanese optical scale 0.82 (delphinus's `MIGU1M_SCALE`).

## Checking a build

An installed SF Mono Square (`~/Library/Fonts/SFMonoSquare-*.otf`) is also
2048 UPM, so bounding-box heights and advances compare directly with
fontTools. Quick spot checks:

- GSUB has `calt` (ligatures survived the later phases).
- 、。 sit left (xMin ≈ 155, LINE Seed's own bearing).
- U+3000 has ink.
- ※ / ★ advance is 1024 (`narrow`) or 2048 (`wide`).
- No icon is taller than its SFMS counterpart.

## Method references

- [delphinus/homebrew-sfmono-square][sfms] — the method this build
  reproduces (square metrics, Propo icons, visible U+3000, bracket
  bearings). The scripts here are original reimplementations; no code is
  vendored from it.
- [The author's Qiita article][qiita] (Japanese) — background on SF Mono
  Square itself.

[sfms]: https://github.com/delphinus/homebrew-sfmono-square
[qiita]: https://qiita.com/delphinus/items/f472eb04ff91daf44274
