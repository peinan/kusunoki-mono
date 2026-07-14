<div align="center">

English | [日本語](README.ja.md)

</div>

# Kusunoki Mono

A personal monospace font for coding with Japanese, built by layering custom
transforms on a [SF Mono Square][sfms]-style base. A full-width CJK glyph is
exactly two Latin columns, so mixed Japanese and code stay aligned.

| Part | Source |
| --- | --- |
| Latin / ASCII / symbols / digits | Apple SF Mono, condensed to the square grid |
| Japanese | LINE Seed JP, with Migu 1M as the fallback |
| Programming ligatures | JetBrains Mono, scaled to the square cell |
| Italic lowercase | 14 letters from Google Sans Code's true italic; the rest stays SF Mono italic, centred |
| Icons | Nerd Fonts v3.4.0, variable width, sized to match SF Mono Square |

## Not distributed — build it yourself

The output embeds Apple SF Mono, which Apple licenses for local use but does
not permit redistributing. Like SF Mono Square itself, this repo therefore
ships no font binaries: it is a build recipe that downloads SF Mono from
Apple plus the OFL/MIT source fonts and builds the font locally on your Mac.

## Install (macOS)

Both routes fetch the sources and build the font on your Mac.

### Homebrew

```sh
brew tap peinan/kusunoki-mono
brew install kusunoki-mono
cp "$(brew --prefix)/share/fonts/KusunokiMono-"*.otf ~/Library/Fonts/
```

### make

Requirements: macOS, [Homebrew][brew], [`uv`][uv]

```sh
brew install fontforge
make setup   # fetch the source fonts and the nerd-fonts patcher
make build   # → build/sfms/dist/KusunokiMono-{Regular,Bold,Italic,BoldItalic}.otf
cp build/sfms/dist/KusunokiMono-*.otf ~/Library/Fonts/
```

Set your terminal or editor font to **Kusunoki Mono**.

## Tuning knobs

Env vars for `make build`; Homebrew scrubs custom env vars, so tune via the
make route:

| Variable | Default | Effect |
| --- | --- | --- |
| `JP_SCALE` | `0.82` | Japanese optical size |
| `LIG_YSCALE` | `1.478` | Ligature height; the default matches tall operators like `//` to SF Mono's `/` |
| `ITALIC_INK_OFFSET` | `0.0` | Italic Latin ink offset as a fraction of the cell; `0` is centred like the upright, `0.076` is SF Mono's native right-lean |
| `GSC_R` / `GSC_B` | `360` / `650` | Google Sans Code weights for the grafted italic letters |
| `KM_AMBIGUOUS_WIDTH` | `narrow` | Cells for East-Asian-ambiguous symbols like ※ ★ ℃; `narrow` is 1 cell and safe in strict terminals like Ghostty, `wide` is 2 cells like SF Mono Square |
| `KM_SFMS_DIR` | `~/Library/Fonts` | Where `SFMonoSquare-*.otf` lives, used to size icons to match; the step is skipped if absent |

## Development

Pipeline internals are documented in [docs/development.md](docs/development.md).

## Licensing

The built font contains Apple SF Mono and is a personal, non-redistributable
artifact. The source fonts keep their own licenses; the build scripts here
are the author's own.

| Source | License |
| --- | --- |
| SF Mono | © Apple |
| Migu 1M | M+ / IPA |
| LINE Seed JP | OFL 1.1 |
| Google Sans Code | OFL 1.1 |
| JetBrains Mono | OFL 1.1 |
| Nerd Fonts | MIT + upstream |

[sfms]: https://github.com/delphinus/homebrew-sfmono-square
[brew]: https://brew.sh/
[uv]: https://docs.astral.sh/uv/
