<div align="center">

English | [日本語](development.ja.md)

</div>

# Development notes

How the build works and why, for changing the pipeline. To just build and
install the font, see the [README](../README.md).

## Layout

| Path | Holds |
| --- | --- |
| `scripts/` | The whole pipeline: `setup.sh` fetches sources, `build.sh` runs the phases, one Python script per transform |
| `sources/` | Fetched inputs, gitignored; versions pinned in `setup.sh` |
| `build/sfms/` | Per-phase intermediates and logs, gitignored |
| `dist/` | The final four OTFs |

FontForge scripts run via `fontforge -script`; the fontTools ones declare
inline dependencies with PEP 723 and run via `uv run`, so there is no venv
to set up. Each script's docstring is its usage reference.

## Pipeline

`build.sh` builds Regular → Bold → Italic → BoldItalic, roughly 2 minutes
per style; each phase logs to `build/sfms/<style>.p<n>.log`.

| Phase | Script | Does |
| --- | --- | --- |
| P1 | `build_base.py` | SF Mono + Migu 1M onto the square grid |
| P2 | nerd-fonts `font-patcher` | Icons, at their natural widths |
| P2.5 | `plan_icon_scale.py` `apply_icon_scale.py` | Shrink icons taller than SF Mono Square |
| P2.6 | `instance_vf.py` `add_ligatures.py` | JetBrains Mono ligatures |
| P3 | `swap_lineseed.py` | Kana and kanji to LINE Seed JP |
| P4 | `graft_italic.py` `center_italic.py` | True-italic lowercase; italic styles only |
| P5 | `finalize.py` | Name table, OS/2, metrics |

### P1 base

SF Mono and Migu 1M merge onto the square grid:

- SF Mono condensed uniformly ×0.809 = 1024/1266: Latin advance 1024 at EM 2048, so a full-width CJK glyph is exactly two columns
- Migu 1M supplies kana, kanji, and CJK punctuation: em 1000→2048, sized by `JP_SCALE`, centred in the full-width cell; half-width katakana in the half cell
- Migu also fills symbols SF Mono lacks, such as ※, arrows, and ★
- Filled symbols take their advance from Unicode East Asian Width — terminals count cells from EAW, not the font; `KM_AMBIGUOUS_WIDTH` decides the ambiguous ones
- U+3000 becomes visible as the intersection of ☐ U+2610 and ✚ U+271A — the Ricty idea SF Mono Square also uses
- Italic styles skew the JP to SF Mono's italic angle

### P2 Nerd icons

The pinned v3.4.0 patcher runs with
`--complete --variable-width-glyphs --careful`:

- The "Propo" mode keeps each icon's natural width and per-set size, like SF Mono Square
- `--single-width-glyphs` would pack every icon into a half cell and shrink non-Powerline icons to about half height — issue #9
- Latin and CJK advances are untouched either way

### P2.5 icon downscale

nerd-fonts v3.4.0 draws some icons taller than the older set inside SF Mono
Square; anything taller than the local SFMS reference under `KM_SFMS_DIR`
shrinks to its height:

- Same-drawing glyphs only — rasterize, crop to ink, normalize, require mask IoU ≥ 0.6; icon sets drift between versions, so resizing a different drawing is meaningless
- Powerline, box drawing, and braille are excluded; they must fill the cell
- The plan is computed once from Regular into `build/sfms/iconscale.json` and reused for every style; each glyph scales about its ink centre, advance kept
- Skipped when no SFMS reference exists; nothing SFMS-derived is committed

### P2.6 ligatures

JetBrains Mono, instanced at wght 400 and 700, provides the ligatures:

- Its `calt` is terminal-safe: leading cells become blank spacers, the last cell holds one wide `.liga` glyph, so a ligature keeps its N columns
- Copied with a non-uniform scale: horizontal is the cell ratio 1024/600, vertical is `LIG_YSCALE`
- The script defaults to an x-height match; the build pins `1.478` so tall operators like `//` match SF Mono's `/` — issue #7
- Italic styles slant the ligatures to the font's angle

### P3 Japanese swap

Kana, katakana, kanji, and CJK punctuation present in both the base and
LINE Seed JP swap over; SF Mono Latin, icons, and the rare kanji LINE Seed
lacks stay:

- Each glyph scales to the base's CJK size, measured on 国永日, centred in the full-width cell, advance kept
- Exceptions from issue #4: 、。 and the full-width brackets keep LINE Seed's own horizontal placement
- Their left side bearing maps proportionally into the cell, so open brackets hug the right and close brackets hug the left

### P4 italic graft

Italic styles only:

- 14 lowercase letters a b c d e f i j k l p v y z come from Google Sans Code's true italic
- Instanced thinner than the target weight via `GSC_R` / `GSC_B` to match SF Mono's stems, x-height-matched, placed at the median ink-centre of the SF Mono letters that stay
- `center_italic.py` then shifts the ASCII so the median ink offset equals `ITALIC_INK_OFFSET` × cell; 0 is centred like the upright, SF Mono's native lean is +7.6%

### P5 finalize

- One family "Kusunoki Mono" with a RIBBI name table
- Vertical metrics 1638/-410 at 2048 UPM, matching SF Mono Square
- PANOSE monospace; Latin and Japanese code pages
- A copyright note recording the font embeds SF Mono and must not be redistributed
- `KM_VERSION` sets the version string

## Sources and pinning

`setup.sh` is idempotent — re-running skips anything already present — and
macOS-only, because Apple's DMG is extracted with hdiutil and pkgutil.

| Source | Pinned to |
| --- | --- |
| SF Mono | Apple's official `SF-Mono.dmg` |
| Migu 1M | The v2020.0307 release zip |
| nerd-fonts FontPatcher | v3.4.0 |
| LINE Seed JP, Google Sans Code, JetBrains Mono | google/fonts `main`, OFL |

## Homebrew tap

The formula lives in [peinan/homebrew-kusunoki-mono][tap]: it stages the same
pinned sources into `sources/` and runs `scripts/build.sh` unchanged, so
`brew install` and `make build` produce the same fonts. The tap also ships a
`font-kusunoki-mono` cask that copies the formula's fonts into
`~/Library/Fonts`. Release flow:

- tag `vX.Y.Z` in this repo
- point the formula's `url` and `sha256` at that tag's tarball
- bump the cask's `version` and `sha256` to the same tag
- until the first tag the formula is head-only, so install needs `--HEAD`

## Metrics cheat sheet

| Metric | Value |
| --- | --- |
| EM | 2048 |
| Latin advance | 1024 = SF Mono's 1266 × 0.809 |
| CJK advance | 2048 |
| Ascent / descent | 1638 / -410, set before the Nerd patch |
| Japanese optical scale | 0.82, delphinus's `MIGU1M_SCALE` |

## Checking a build

An installed SF Mono Square under `~/Library/Fonts` is also 2048 UPM, so
bounding-box heights and advances compare directly with fontTools. Quick
spot checks:

- GSUB still has `calt` after the later phases
- 、。 sit left; xMin ≈ 155 is LINE Seed's own bearing
- U+3000 has ink
- ※ and ★ advance 1024 for `narrow`, 2048 for `wide`
- No icon taller than its SFMS counterpart

## Method references

- [delphinus/homebrew-sfmono-square][sfms] — the method this build
  reproduces: square metrics, Propo icons, visible U+3000, bracket
  bearings. The scripts here are original reimplementations; no code is
  vendored from it
- [The author's Qiita article][qiita], in Japanese — background on SF Mono
  Square itself

[tap]: https://github.com/peinan/homebrew-kusunoki-mono
[sfms]: https://github.com/delphinus/homebrew-sfmono-square
[qiita]: https://qiita.com/delphinus/items/f472eb04ff91daf44274
