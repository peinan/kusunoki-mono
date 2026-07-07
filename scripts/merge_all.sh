#!/usr/bin/env bash
# Merge Iosevka + LINE Seed JP (+ Nerd) into one variant's TTFs, one per style.
# The variant is selected by NERD_FONTS / LIGATURES in the environment (config.sh
# turns those into FAMILY / FONT_BASENAME / VARIANT_DIR).
set -euo pipefail
cd "$(dirname "$0")/.."
source ./config.sh
mkdir -p "$BUILD_DIR/jp" "$VARIANT_DIR"

echo "==> Variant '$FAMILY'  (NERD_FONTS=$NERD_FONTS LIGATURES=$LIGATURES) -> $VARIANT_DIR"
for style in $STYLES; do
  iose="$BUILD_DIR/iosevka/$(iosevka_file "$style")"
  [ -s "$iose" ] || { echo "ERROR: missing Iosevka TTF: $iose (run 'make iosevka')" >&2; exit 1; }
  jp="$BUILD_DIR/jp/${FONT_BASENAME}-${style}.ttf"
  out="$VARIANT_DIR/${FONT_BASENAME}-${style}.ttf"
  echo "==> [$FONT_BASENAME/$style] FontForge: transform BIZ + Nerd"
  fontforge -quiet -script scripts/merge.py "$style" "$jp"
  echo "==> [$FONT_BASENAME/$style] fontTools: merge + fix"
  uv run scripts/fix.py "$iose" "$jp" "$out" "$style"
done
echo "==> merge complete -> $VARIANT_DIR"
