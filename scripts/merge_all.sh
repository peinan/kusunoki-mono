#!/usr/bin/env bash
# Merge Iosevka + BIZ UDGothic + Nerd Fonts into dist/ TTFs, one per style.
set -euo pipefail
cd "$(dirname "$0")/.."
source ./config.sh
mkdir -p "$BUILD_DIR/jp" "$DIST_DIR"

for style in $STYLES; do
  iose="$BUILD_DIR/iosevka/$(iosevka_file "$style")"
  [ -s "$iose" ] || { echo "ERROR: missing Iosevka TTF: $iose (run 'make iosevka')" >&2; exit 1; }
  jp="$BUILD_DIR/jp/jp-${style}.ttf"
  out="$DIST_DIR/${BUILD_PLAN}-${style}.ttf"
  echo "==> [$style] FontForge: transform BIZ + Nerd"
  fontforge -quiet -script scripts/merge.py "$style" "$jp"
  echo "==> [$style] fontTools: merge + fix"
  uv run scripts/fix.py "$iose" "$jp" "$out" "$style"
done
echo "==> merge complete -> $DIST_DIR"
