# Screenshot sources

Rendered with the built font. After `make build`, regenerate with:

```sh
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
cd docs/images/src
"$CHROME" --headless=new --hide-scrollbars --window-size=1760,500  --screenshot=../hero.png      hero.html
"$CHROME" --headless=new --hide-scrollbars --window-size=1760,1140 --screenshot=../sample.png    sample.html
"$CHROME" --headless=new --hide-scrollbars --window-size=1760,480  --screenshot=../grid.png      grid.html
"$CHROME" --headless=new --hide-scrollbars --window-size=1760,400  --screenshot=../ligatures.png ligatures.html
```
