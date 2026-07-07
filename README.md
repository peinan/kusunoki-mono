<div align="center">

English | [日本語](README.ja.md)

</div>

# Kusunoki Mono

[![License: OFL 1.1](https://img.shields.io/badge/license-OFL--1.1-blue.svg)](OFL.txt)

A monospace font for coding with Japanese. It merges [Iosevka][iosevka] for
Latin / ASCII / symbols / ligatures, [LINE Seed JP][lineseed] for Japanese kana and
kanji, and [Nerd Fonts][nerd] for terminal icons — with the CJK glyphs sized to
exactly two Latin columns so text stays aligned.

![Kusunoki Mono specimen](docs/images/specimen.png)

## Features

- **Aligned** — a full-width CJK glyph is exactly two Latin columns, so mixed Japanese and code stay on the grid.
- **Legible glyphs** — a slashed zero and Iosevka's `ss14` design keep `0 O` and `1 l I` distinct.
- **Ligatures** — `=> != >= <= |> ->` and friends (the `LG` / `NFLG` variants; each ligature group is configurable).
- **Nerd Font icons** — Powerline and terminal glyphs (the `NF` / `NFLG` variants).
- **Visible ideographic space** — U+3000 is drawn as a faint box.
- **Four styles** — Regular / Bold / Italic / Bold Italic, with the CJK slanted to match the Latin italic.

## Which one to download

Four variants, each in **Regular / Bold / Italic / Bold Italic**. They use
different family names, so you can install several side by side and choose per app.

| Font family            | Ligatures | Nerd Font icons | Good for                              |
| ---------------------- | :-------: | :-------------: | ------------------------------------- |
| **Kusunoki Mono**      |     –     |        –        | Plain, maximally compatible           |
| **Kusunoki Mono NF**   |     –     |        ✓        | Terminals with icons, no ligatures    |
| **Kusunoki Mono LG**   |     ✓     |        –        | Editors, with ligatures               |
| **Kusunoki Mono NFLG** |     ✓     |        ✓        | Everything — ligatures **and** icons  |

Not sure? Pick **NFLG** for a terminal/editor that shows icons and ligatures, or
plain **Kusunoki Mono** if you want neither.

## Install

1. Download a variant's zip from the [Releases page][releases].
2. Install the `.ttf` files:
   - **macOS** — open them and click *Install*, or copy to `~/Library/Fonts/`.
   - **Windows** — select them, right-click → *Install*.
   - **Linux** — copy to `~/.local/share/fonts/`, then `fc-cache -f`.
3. Set your editor/terminal font to the family name, e.g. `Kusunoki Mono NFLG`.

Ligatures (the `LG` / `NFLG` variants) usually need turning on in your app too —
e.g. VS Code `"editor.fontLigatures": true`. The plain / `NF` variants have no
ligatures at all, which some people prefer in a terminal.

## Tweak it yourself

You only need this to change something — the released fonts work as-is.

Requirements: macOS + [Homebrew][brew], [`uv`][uv], Node.js ≥ 18, and an
[Iosevka][iosevka] checkout next to this repo at `../Iosevka` (or set `IOSEVKA_DIR`).

```sh
make setup   # one-time: install tools, download LINE Seed JP + Nerd Fonts
make build   # build one variant → dist/<Family>/
make verify  # open dist/<Family>/specimen.html to eyeball the result
```

Two knobs cover most tastes:

- **Density** — `WIDTH_EM` in `config.sh`: `0.6` (roomier, default) or `0.5`
  (tighter; full-width CJK = exactly 1em). Then `make && make verify`.
- **Ligatures** — which ligatures fire is the `[buildPlans.KusunokiMono.ligations]`
  table in `private-build-plans.toml` (`inherits` / `enables` / `disables`). Then
  `make && make verify`.

Full build pipeline, the variant matrix, and the release/CI setup are in
[docs/BUILD.md](docs/BUILD.md).

## Built from

- [Iosevka][iosevka] — Latin, ASCII, symbols, box drawing, ligatures (OFL 1.1)
- [LINE Seed JP][lineseed] — Japanese kana & kanji (OFL 1.1)
- [Nerd Fonts][nerd] — icon glyphs (MIT + upstream glyph licenses)

## License

[SIL Open Font License 1.1](OFL.txt). "Kusunoki Mono" is a new name and is not a
reserved name of any of the source fonts.

[iosevka]: https://github.com/be5invis/Iosevka
[lineseed]: https://seed.line.me/
[nerd]: https://www.nerdfonts.com/
[releases]: https://github.com/peinan/kusunoki/releases
[brew]: https://brew.sh/
[uv]: https://docs.astral.sh/uv/
