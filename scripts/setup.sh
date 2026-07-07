#!/usr/bin/env bash
# Install toolchain, download font sources, and prepare the Iosevka checkout.
set -euo pipefail
cd "$(dirname "$0")/.."
source ./config.sh

echo "==> System tools (fontforge, ttfautohint)"
missing=()
for t in fontforge ttfautohint; do command -v "$t" >/dev/null 2>&1 || missing+=("$t"); done
if [ ${#missing[@]} -eq 0 ]; then
  echo "    ok: fontforge, ttfautohint present"
elif command -v brew >/dev/null 2>&1; then
  brew install "${missing[@]}"
elif command -v apt-get >/dev/null 2>&1; then
  sudo apt-get update -qq
  sudo apt-get install -y fontforge python3-fontforge ttfautohint unzip zip
else
  echo "ERROR: need Homebrew or apt-get to install: ${missing[*]}" >&2; exit 1
fi

command -v uv >/dev/null 2>&1 || { echo "ERROR: uv not found — install uv first" >&2; exit 1; }
echo "    ok: uv $(uv --version)"

echo "==> Font sources into $SOURCES_DIR"
mkdir -p "$SOURCES_DIR/lineseed-jp" "$SOURCES_DIR/nerd"

lsjp_base="https://raw.githubusercontent.com/google/fonts/main/ofl/lineseedjp"
for f in LINESeedJP-Regular.ttf LINESeedJP-Bold.ttf OFL.txt; do
  dest="$SOURCES_DIR/lineseed-jp/$f"
  [ -s "$dest" ] || { echo "    fetching $f"; curl -fsSL "$lsjp_base/$f" -o "$dest"; }
done

if [ "${NERD_FONTS}" = "1" ]; then
  nerd_ttf="$SOURCES_DIR/nerd/SymbolsNerdFontMono-Regular.ttf"
  if [ ! -s "$nerd_ttf" ]; then
    echo "    fetching Nerd Fonts SymbolsOnly"
    zip="$SOURCES_DIR/nerd/NerdFontsSymbolsOnly.zip"
    curl -fsSL "https://github.com/ryanoasis/nerd-fonts/releases/latest/download/NerdFontsSymbolsOnly.zip" -o "$zip"
    unzip -o "$zip" "SymbolsNerdFontMono-Regular.ttf" -d "$SOURCES_DIR/nerd/"
    rm -f "$zip"
  fi
fi

echo "==> npm install in $IOSEVKA_DIR"
( cd "$IOSEVKA_DIR" && npm install )

echo "==> setup complete"
