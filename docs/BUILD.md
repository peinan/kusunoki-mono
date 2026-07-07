<div align="center">

English | [日本語](BUILD.ja.md)

</div>

# Building & releasing Kusunoki Mono

Maintainer notes. For install & usage, see the [README](../README.md).

## How it fits together

1. **Iosevka** is built once from `private-build-plans.toml` (peinan's design:
   `ss14` + `cv` overrides, ligatures on, `exportGlyphNames`, and `noCvSs` to drop
   unused alternate glyphs so the merged font stays under TrueType's 65535-glyph
   limit). This is the Latin / ASCII / symbol / box-drawing / ligature base.
2. **LINE Seed JP** and **Nerd Fonts** are transformed in FontForge
   (`scripts/merge.py`): rescaled to 1000 UPM, width-normalized so a full-width
   CJK glyph spans exactly two Latin cells, and (for italics) faux-slanted about
   each glyph's own centre.
3. **fontTools** (`scripts/fix.py`) drops anything Iosevka already covers, merges
   with Iosevka first — so Iosevka's ligature GSUB is preserved verbatim — and
   fixes the `name` / `OS/2` (CP932, USE_TYPO_METRICS) / `post` (isFixedPitch) /
   vertical-metric tables.
4. `scripts/specimen.py` asserts the metrics and writes a specimen HTML.

Iosevka is only ever built once; the four variants differ solely in the merge stage.

## Requirements

- macOS (Homebrew) or Linux (apt) — `fontforge`, `ttfautohint`
- [`uv`](https://docs.astral.sh/uv/) for `fonttools`
- Node.js ≥ 18 and an Iosevka checkout at `../Iosevka` (or set `IOSEVKA_DIR`)

`make setup` installs the system tools (via brew or apt), downloads the source
fonts, and runs `npm install` in the Iosevka checkout.

## Commands

| Command         | What                                                          |
| --------------- | ------------------------------------------------------------ |
| `make setup`    | Install deps, download LINE Seed JP + Nerd Fonts, npm install |
| `make iosevka`  | Build the Iosevka base (shared by all variants)              |
| `make build`    | One variant (iosevka + merge) — local iteration             |
| `make variants` | All four variants (run `make iosevka` first)                |
| `make package`  | Zip each variant → `dist/release-assets/`                    |
| `make dist-all` | `iosevka` + `variants` + `package`                          |
| `make verify`   | Metric assertions + specimen for the current variant        |

## Variants

Two axes, set via the environment (`config.sh` derives the family name, basename,
and output dir from them):

- `NERD_FONTS` = `1`/`0` — merge Nerd Fonts icon glyphs.
- `LIGATURES` = `1`/`0` — keep Iosevka's default `calt` ligatures. For `0`, `calt`
  is unhooked from the GSUB LangSys at merge time (`fix.py`); Iosevka is **not**
  rebuilt.

Naming is additive — the base has neither feature, `NF` adds icons, `LG` adds
ligatures:

| `NERD_FONTS` | `LIGATURES` | Family                |
| :----------: | :---------: | --------------------- |
|      0       |      0      | `Kusunoki Mono`       |
|      1       |      0      | `Kusunoki Mono NF`    |
|      0       |      1      | `Kusunoki Mono LG`    |
|      1       |      1      | `Kusunoki Mono NFLG`  |

## Configuration

- `config.sh` — merge-side knobs: `VERSION`, `WIDTH_EM` (`0.6`/`0.5`), `TARGET_EM`,
  `ITALIC_ANGLE`, `STYLES`, `NERD_FONTS`, `LIGATURES`, and vertical-harmony tuning
  (`CJK_Y_SCALE` / `CJK_Y_SHIFT`).
- `private-build-plans.toml` — the Iosevka design (variants, `ligations`,
  `exportGlyphNames`, weights, widths, slopes).

## Releases (CI)

`.github/workflows/release.yml` builds all four variants and publishes them to a
GitHub Release. It triggers on a **`v*` tag push** (the tag names the release) or
a manual **workflow_dispatch** run (which releases `v<VERSION>` from `config.sh`).
Plain pushes to `main` do not release, so work-in-progress can land freely.

**To cut a release:** bump `VERSION` in `config.sh`, commit, then push a matching
tag:

```sh
git tag v0.4.0
git push origin v0.4.0
```
