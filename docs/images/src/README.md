# Screenshot sources

Rendered with the built font. After `make build`, regenerate with:

```sh
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
cd docs/images/src
"$CHROME" --headless=new --hide-scrollbars --window-size=1760,500  --screenshot=../hero.png      hero.html
"$CHROME" --headless=new --hide-scrollbars --window-size=1760,1220 --screenshot=../specimen.png  specimen.html
"$CHROME" --headless=new --hide-scrollbars --window-size=1760,480  --screenshot=../grid.png      grid.html
"$CHROME" --headless=new --hide-scrollbars --window-size=1760,560  --screenshot=../ligatures.png ligatures.html
```

`editor-sample.py` is not a page: open it in a real editor and screenshot it
(turn on `editor.fontLigatures` and an italic-comments theme first).
