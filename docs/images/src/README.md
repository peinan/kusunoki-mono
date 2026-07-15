# Screenshot sources

Rendered with the built font. After `make build`, regenerate with:

```sh
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
cd docs/images/src
"$CHROME" --headless=new --hide-scrollbars --window-size=1760,500  --screenshot=../hero.png     hero.html
"$CHROME" --headless=new --hide-scrollbars --window-size=1694,1668 --screenshot=../specimen.png specimen.html
"$CHROME" --headless=new --hide-scrollbars --window-size=2560,1280 --screenshot=../og.png       og.html
```

`editor-sample.py` is not a page: open it in a real editor and screenshot it
(turn on `editor.fontLigatures` and an italic-comments theme first).
