# Kusunoki Mono

A programming monospace font that merges **Iosevka** (Latin / ASCII / symbols / ligatures)
with **BIZ UDGothic** (Japanese kana & kanji) and **Nerd Fonts** (icon glyphs).

> Status: in development.

## Requirements

- macOS with [Homebrew](https://brew.sh/) (for `fontforge`, `ttfautohint`)
- [`uv`](https://docs.astral.sh/uv/) (Python tooling — `fonttools` etc.)
- Node.js ≥ 18 and an Iosevka checkout at `../Iosevka` (override via `IOSEVKA_DIR`)

## Build

```sh
make setup     # install deps + download BIZ UDGothic / Nerd Fonts + npm install
make build     # build custom Iosevka, then merge → dist/
make verify    # metric assertions + specimen (HTML / PNG)
```

## Configuration

- **Merge knobs** — cell width, styles, toggles: `config.sh`
- **Iosevka design** — variants, cv##, ligatures: `private-build-plans.toml`

### Change the cell width (density)

Edit `WIDTH_EM` in `config.sh` (`0.6` ↔ `0.5`), then:

```sh
make && make verify
```

`0.6` keeps the wider Latin cell from the gist (full-width CJK advance = 1.2em).
`0.5` is the conventional dense layout (full-width CJK = 1.0em exactly).

### Change ligatures

Edit `[buildPlans.KusunokiMono.ligations]` in `private-build-plans.toml`
(`inherits` / `enables` / `disables`), then `make && make verify`.

## License

SIL Open Font License 1.1. Built from Iosevka (OFL), BIZ UDGothic (OFL), and
Nerd Fonts (MIT + upstream glyph licenses). See `OFL.txt`.
