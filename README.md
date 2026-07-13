<div align="center">

English | [日本語](README.ja.md)

</div>

# Kusunoki Mono (SF Mono Square edition)

A personal monospace font for coding with Japanese, built by layering custom
transforms on a [SF Mono Square][sfms]-style base:

- **Latin / ASCII / symbols / digits** — Apple **SF Mono**, condensed to a
  square grid (a full-width CJK glyph is exactly two Latin columns, so mixed
  Japanese and code stay aligned).
- **Japanese** — **LINE Seed JP**, with **Migu 1M** as the fallback for the
  kana / kanji it doesn't cover.
- **Ligatures** — **JetBrains Mono**'s programming ligatures (`->` `=>` `!=` …),
  scaled to the square cell.
- **Italic** — 14 lowercase letters grafted from **Google Sans Code**'s true
  italic; the rest is SF Mono's italic, centred in the cell.
- **Icons** — **Nerd Fonts** (official v3.4.0 patcher, variable-width — icons
  sized to match SF Mono Square).

## Not distributed — build it yourself

The output **embeds Apple SF Mono**, which Apple licenses for local use but
does **not** permit redistributing. So no font binaries are shipped here —
like SF Mono Square itself, this repo is a **build recipe**: it downloads
SF Mono from Apple plus the OFL/MIT source fonts and builds the font locally
on your Mac.

## Build (macOS)

Requirements: macOS, [Homebrew][brew] (`brew install fontforge`), and
[`uv`][uv].

```sh
make setup   # fetch SF Mono (Apple), Migu 1M, LINE Seed JP, Google Sans Code, JetBrains Mono, nerd-fonts patcher
make build   # → build/sfms/dist/KusunokiMono-{Regular,Bold,Italic,BoldItalic}.otf
```

Install the four `.otf` into `~/Library/Fonts/` and set your terminal / editor
font to **Kusunoki Mono**.

## Tuning knobs

Env vars for `make build`:

- `JP_SCALE` — Japanese optical size (default `0.82`).
- `LIG_YSCALE` — ligature height (default `1.478`, tuned so tall operators
  like `//` match SF Mono's `/`; lower it if ligatures read too tall).
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

## Development

Pipeline internals — the phases, the scripts, the metrics, and the method
references — are in [docs/development.md](docs/development.md).

## Licensing

The built font is a **personal, non-redistributable** artifact — it contains
Apple SF Mono. The source fonts keep their own licenses: SF Mono (© Apple),
Migu 1M (M+ / IPA), LINE Seed JP (OFL 1.1), Google Sans Code (OFL 1.1),
JetBrains Mono (OFL 1.1), Nerd Fonts (MIT + upstream). The build scripts here
are the author's own.

[sfms]: https://github.com/delphinus/homebrew-sfmono-square
[brew]: https://brew.sh/
[uv]: https://docs.astral.sh/uv/
