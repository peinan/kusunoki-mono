<div align="center">

English | [日本語](README.ja.md)

</div>

# Kusunoki Mono (SF Mono Square edition)

A personal monospace font for coding with Japanese, built by layering custom
transforms on a [SF Mono Square][sfms]-style base:

- **Latin / ASCII / symbols / digits** — Apple **SF Mono**, condensed to a
  square grid (a full-width CJK glyph is exactly two Latin columns, so mixed
  Japanese and code stay aligned).
- **Japanese** — **LINE Seed JP** for the kana / kanji it covers, **Migu 1M**
  as the fallback for the rest.
- **Italic** — 14 lowercase letters grafted from **Google Sans Code**'s true
  italic; the rest is SF Mono's italic, centred in the cell.
- **Icons** — **Nerd Fonts** (official v3.4.0 patcher, variable-width — icons
  sized to match SF Mono Square).

## Not distributed — build it yourself

The output **embeds Apple SF Mono**, which Apple licenses for local use but
does **not** permit redistributing. So no font binaries are shipped here — this
repo is a **build recipe** that downloads SF Mono from Apple plus the
OFL/MIT source fonts and builds the font locally on your Mac.

## Build (macOS)

Requirements: macOS, [Homebrew][brew] (`brew install fontforge`), and
[`uv`][uv].

```sh
make setup   # fetch SF Mono (Apple), Migu 1M, nerd-fonts patcher, LINE Seed JP, Google Sans Code
make build   # → build/sfms/dist/KusunokiMono-{Regular,Bold,Italic,BoldItalic}.otf
```

Install the four `.otf` into `~/Library/Fonts/` and set your terminal / editor
font to **Kusunoki Mono**.

Tuning knobs (env vars for `make build`):

- `JP_SCALE` — Japanese optical size (default `0.82`).
- `ITALIC_INK_OFFSET` — italic Latin ink offset as a fraction of the cell
  (`0.0` = centred like the upright [default]; `0.076` = SF Mono's native
  right-lean).
- `GSC_R` / `GSC_B` — Google Sans Code weight for the grafted italic letters.
- `KM_AMBIGUOUS_WIDTH` — cell width of East-Asian-ambiguous symbols like `※ ★ ℃`:
  `narrow` (default) makes them 1 cell so they don't overlap in strict terminals
  (Ghostty); `wide` makes them 2 cells (like SF Mono Square, for terminals set to
  treat ambiguous width as wide).
- `KM_SFMS_DIR` — directory holding `SFMonoSquare-*.otf`, used to size icons to
  match SF Mono Square (default `~/Library/Fonts`; the step is skipped if absent).

## How it's built

`scripts/sfmono/`, orchestrated by `build.sh`:

1. `build_base.py` — SF Mono ×0.809 (square) + Migu 1M ×0.82; also fills symbols
   SF Mono lacks (※, arrows, …) from Migu → base.
2. nerd-fonts `font-patcher --variable-width-glyphs` → icons (CJK stays full-width).
3. `plan_icon_scale.py` + `apply_icon_scale.py` — shrink icons taller than SF Mono
   Square to match it (same-glyph only; needs a local SFMS ref, else skipped).
4. `swap_lineseed.py` — swap kana/kanji to LINE Seed JP (Migu fallback).
5. `graft_italic.py` + `center_italic.py` — Google Sans Code italic letters, centred.
6. `finalize.py` — RIBBI name / OS2 / metrics.

Deps are just `fontforge` + `uv` (fonttools) + the nerd-fonts patcher fetched
by `setup.sh`.

## Licensing

The built font is a **personal, non-redistributable** artifact — it contains
Apple SF Mono. The source fonts keep their own licenses: SF Mono (© Apple), Migu
1M (M+ / IPA), LINE Seed JP (OFL 1.1), Google Sans Code (OFL 1.1), Nerd Fonts
(MIT + upstream). The build scripts here are the author's own.

[sfms]: https://github.com/delphinus/homebrew-sfmono-square
[brew]: https://brew.sh/
[uv]: https://docs.astral.sh/uv/
