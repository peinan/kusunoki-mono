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
make build     # build one variant (Iosevka + merge) for local iteration → dist/<Variant>/
make verify    # metric assertions + specimen.html for the current variant
make dist-all  # build the base + all 4 release variants + zip them → dist/release-assets/
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

## Variants

Four variants are produced (each in Regular / Bold / Italic / Bold Italic),
distinguished by family name so they install side by side:

| Family name         | Nerd Fonts | Ligatures |
| ------------------- | :--------: | :-------: |
| Kusunoki Mono       |     –      |     ✓     |
| Kusunoki Mono NF    |     ✓      |     ✓     |
| Kusunoki Mono NL    |     –      |     –     |
| Kusunoki Mono NF NL |     ✓      |     –     |

The axes are `NERD_FONTS` (1/0) and `LIGATURES` (1/0). No-ligature variants reuse
the same Iosevka build — the default `calt` feature is unhooked at merge time, so
Iosevka is only built once.

## Releases (CI)

`.github/workflows/release.yml` runs on every push/merge to `main`: it builds all
four variants and publishes them to a GitHub Release tagged `v<VERSION>` (from
`config.sh`), replacing the assets. Bump `VERSION` to cut a new release; pushes
without a bump refresh the current version's assets. Docs-only (`**.md`) pushes
are skipped, and the workflow can be triggered manually (workflow_dispatch).

## License

SIL Open Font License 1.1. Built from Iosevka (OFL), BIZ UDGothic (OFL), and
Nerd Fonts (MIT + upstream glyph licenses). See `OFL.txt`.
