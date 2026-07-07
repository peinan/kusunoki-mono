#!/usr/bin/env bash
# Zip each built variant into dist/release-assets/<FontBasename>-v<VERSION>.zip
# (TTFs + OFL.txt). Run after `make variants`.
set -euo pipefail
cd "$(dirname "$0")/.."
source ./config.sh

assets="$DIST_DIR/release-assets"
rm -rf "$assets"; mkdir -p "$assets"

for nerd in 1 0; do
  for liga in 1 0; do
    (
      export NERD_FONTS=$nerd LIGATURES=$liga
      source ./config.sh
      [ -d "$VARIANT_DIR" ] && ls "$VARIANT_DIR"/*.ttf >/dev/null 2>&1 || {
        echo "skip (not built): $FONT_BASENAME"; exit 0; }
      zip="$assets/${FONT_BASENAME}-v${VERSION}.zip"
      zip -qj "$zip" "$VARIANT_DIR"/*.ttf "$ROOT_DIR/OFL.txt"
      echo "packaged $(basename "$zip")  ($(cd "$VARIANT_DIR" && ls *.ttf | wc -l | tr -d ' ') styles)"
    )
  done
done
echo "==> release assets in $assets"
ls -1 "$assets"
