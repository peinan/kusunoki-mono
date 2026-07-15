#!/usr/bin/env bash
# Fetch every source the SF Mono Square build needs. Self-contained and
# idempotent — re-running skips anything already present.
#
#   scripts/setup.sh
#
# macOS only (uses hdiutil / pkgutil to extract Apple's SF Mono). Set
# SOURCES_DIR to fetch into a different directory (used by tests).
set -uo pipefail
cd "$(dirname "$0")/.."

SRC="${SOURCES_DIR:-sources}"
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15) curl"

# --- pinned source versions --------------------------------------------------
SFMONO_DMG="https://devimages-cdn.apple.com/design/resources/download/SF-Mono.dmg"
MIGU_ZIP="https://github.com/itouhiro/mixfont-mplus-ipa/releases/download/v2020.0307/migu-1m-20200307.zip"
NERD_VER="v3.4.0"
NERD_ZIP="https://github.com/ryanoasis/nerd-fonts/releases/download/${NERD_VER}/FontPatcher.zip"
GF="https://raw.githubusercontent.com/google/fonts/main/ofl"

echo "==> checking tools"
for t in fontforge uv curl unzip hdiutil pkgutil; do
  command -v "$t" >/dev/null 2>&1 || { echo "ERROR: '$t' not found" >&2; exit 1; }
done

mkdir -p "$SRC"

# --- SF Mono (Apple; personal use only, never redistributed) -----------------
if [ ! -s "$SRC/sf-mono/SF-Mono-Regular.otf" ]; then
  echo "==> SF Mono (Apple)"
  mkdir -p "$SRC/sf-mono"
  tmp="$(mktemp -d)"
  curl -fsSL -o "$tmp/SF-Mono.dmg" "$SFMONO_DMG"
  mp="$(hdiutil attach "$tmp/SF-Mono.dmg" -nobrowse -readonly | grep -oE '/Volumes/[^"]*$' | tail -1)"
  pkg="$(find "$mp" -name '*.pkg' | head -1)"
  pkgutil --expand-full "$pkg" "$tmp/pkg" >/dev/null
  cp $(find "$tmp/pkg" -name 'SF-Mono-*.otf') "$SRC/sf-mono/"
  hdiutil detach "$mp" >/dev/null
  /bin/rm -rf "$tmp"
else
  echo "==> SF Mono present"
fi

# --- Migu 1M (Japanese base + fallback) --------------------------------------
if [ ! -s "$SRC/migu-1m/migu-1m-regular.ttf" ]; then
  echo "==> Migu 1M"
  mkdir -p "$SRC/migu-1m"
  tmp="$(mktemp -d)"
  curl -fsSL -A "$UA" -o "$tmp/migu.zip" "$MIGU_ZIP"
  unzip -o -j "$tmp/migu.zip" '*migu-1m-regular.ttf' '*migu-1m-bold.ttf' -d "$SRC/migu-1m/" >/dev/null
  /bin/rm -rf "$tmp"
else
  echo "==> Migu 1M present"
fi

# --- Nerd Fonts font-patcher --------------------------------------------------
if [ ! -x "$SRC/nerd-patcher/font-patcher" ]; then
  echo "==> Nerd Fonts font-patcher ${NERD_VER}"
  mkdir -p "$SRC/nerd-patcher"
  tmp="$(mktemp -d)"
  curl -fsSL -o "$tmp/FontPatcher.zip" "$NERD_ZIP"
  unzip -o -q "$tmp/FontPatcher.zip" -d "$SRC/nerd-patcher/"
  /bin/rm -rf "$tmp"
else
  echo "==> Nerd font-patcher present"
fi

# --- LINE Seed JP (primary kana/kanji) ---------------------------------------
if [ ! -s "$SRC/lineseed-jp/LINESeedJP-Regular.ttf" ]; then
  echo "==> LINE Seed JP"
  mkdir -p "$SRC/lineseed-jp"
  for f in LINESeedJP-Regular.ttf LINESeedJP-Bold.ttf OFL.txt; do
    curl -fsSL "$GF/lineseedjp/$f" -o "$SRC/lineseed-jp/$f"
  done
else
  echo "==> LINE Seed JP present"
fi

# --- Google Sans Code (italic VF, for the italic letter graft) ---------------
if [ ! -s "$SRC/google-sans-code/GoogleSansCode-Italic[wght].ttf" ]; then
  echo "==> Google Sans Code (italic)"
  mkdir -p "$SRC/google-sans-code"
  curl -fsSL -g "$GF/googlesanscode/GoogleSansCode-Italic%5Bwght%5D.ttf" \
    -o "$SRC/google-sans-code/GoogleSansCode-Italic[wght].ttf"
  curl -fsSL "$GF/googlesanscode/OFL.txt" -o "$SRC/google-sans-code/OFL.txt"
else
  echo "==> Google Sans Code present"
fi

# --- JetBrains Mono (programming-ligature designs) ---------------------------
if [ ! -s "$SRC/jetbrains-mono/JetBrainsMono[wght].ttf" ]; then
  echo "==> JetBrains Mono"
  mkdir -p "$SRC/jetbrains-mono"
  curl -fsSL -g "$GF/jetbrainsmono/JetBrainsMono%5Bwght%5D.ttf" \
    -o "$SRC/jetbrains-mono/JetBrainsMono[wght].ttf"
  curl -fsSL "$GF/jetbrainsmono/OFL.txt" -o "$SRC/jetbrains-mono/OFL.txt"
else
  echo "==> JetBrains Mono present"
fi

echo "==> setup complete: $SRC"
ls -1 "$SRC"
