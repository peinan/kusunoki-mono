# Screenshot sources

Rendered with the built font. After `make build`, regenerate with:

```sh
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
cd docs/images/src
"$CHROME" --headless=new --hide-scrollbars --window-size=1760,500  --screenshot=../hero.png     hero.html
"$CHROME" --headless=new --hide-scrollbars --window-size=1694,1724 --screenshot=../specimen.png specimen.html
"$CHROME" --headless=new --hide-scrollbars --window-size=2560,1280 --screenshot=../og.png       og.html
```

`editor-sample.py` is not a page: open it in a real editor and screenshot it
(turn on `editor.fontLigatures` and an italic-comments theme first).
Quantize heavy captures before committing — text and flat UI survive it
untouched: `pngquant --quality=85-98 --speed 1 --ext .png --force <file>`.

## Landing page images (`lp/` → `../lp/`)

The `dakuten-before` shot needs a "before" font (the pre-#20 pipeline: raw
LINE Seed, no P2.8 mark enlarge). Build it once from the P2.6 intermediates
that `make build` leaves in `build/sfms/lig/`, from the repo root:

```sh
mkdir -p build/lp-before
uv run scripts/swap_lineseed.py build/sfms/lig/KusunokiMono-Regular.otf \
  build/lp-before/stage.otf sources/lineseed-jp/LINESeedJP-Regular.ttf Regular
uv run scripts/finalize.py build/lp-before/stage.otf \
  build/lp-before/KusunokiMono-Regular.otf Regular
```

It stays under `build/` and must not be committed (it embeds SF Mono).
Then render the shots; the toggled variants are query params on one page:

```sh
cd docs/images/src/lp
shot() { "$CHROME" --headless=new --hide-scrollbars --window-size="$1" --screenshot="../../lp/$2" "$3"; }
shot 1240,560 grid.png           "file://$PWD/grid.html"
shot 1240,420 liga-on.png        "file://$PWD/liga.html"
shot 1240,420 liga-off.png       "file://$PWD/liga.html?off"
shot 1240,420 italic-km.png      "file://$PWD/italic.html"
shot 1240,420 italic-sf.png      "file://$PWD/italic.html?sf"
shot 1240,560 dakuten-after.png  "file://$PWD/dakuten.html"
shot 1240,560 dakuten-before.png "file://$PWD/dakuten.html?before"
shot 1240,420 nerd.png           "file://$PWD/nerd.html"
shot 1240,560 sizes.png          "file://$PWD/sizes.html"
```

`../lp/tuner.mp4` is a live screen recording, not a page: run
`uv run scripts/dakuten_tuner.py`, then screen-record the editor interaction.
From the repository root, encode the recording with:

```sh
ffmpeg -hide_banner -y -i tuner-raw.mp4 -vf 'fps=24,scale=1360:-2' -c:v libx264 -preset veryslow -crf 28 -pix_fmt yuv420p -an -movflags +faststart docs/images/lp/tuner.mp4
```
