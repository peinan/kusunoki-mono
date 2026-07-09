#!/usr/bin/env bash
# Merge Iosevka + IBM Plex Sans JP (+ Nerd) into one variant's TTFs, one per style.
# The variant is selected by NERD_FONTS / LIGATURES in the environment (config.sh
# turns those into FAMILY / FONT_BASENAME / VARIANT_DIR).
#
# Styles are fully independent (each writes its own TTF), so they build
# concurrently — one fontforge + one fix.py per style, each single-threaded. A
# variant has at most four styles, so this is at most four parallel jobs. Each
# job's output is captured to a log and printed after it finishes so the parallel
# logs don't interleave; any failing style fails the whole merge.
set -euo pipefail
cd "$(dirname "$0")/.."
source ./config.sh
mkdir -p "$BUILD_DIR/jp" "$VARIANT_DIR"

echo "==> Variant '$FAMILY'  (NERD_FONTS=$NERD_FONTS LIGATURES=$LIGATURES) -> $VARIANT_DIR"

pids=()
logs=()
names=()
for style in $STYLES; do
  iose="$BUILD_DIR/iosevka/$(iosevka_file "$style")"
  [ -s "$iose" ] || { echo "ERROR: missing Iosevka TTF: $iose (run 'make iosevka')" >&2; exit 1; }
  jp="$BUILD_DIR/jp/${FONT_BASENAME}-${style}.ttf"
  out="$VARIANT_DIR/${FONT_BASENAME}-${style}.ttf"
  log="$BUILD_DIR/jp/${FONT_BASENAME}-${style}.merge.log"
  echo "==> [$FONT_BASENAME/$style] merging (background)"
  (
    set -euo pipefail
    fontforge -quiet -script scripts/merge.py "$style" "$jp"
    uv run scripts/fix.py "$iose" "$jp" "$out" "$style"
  ) >"$log" 2>&1 &
  pids+=("$!")
  logs+=("$log")
  names+=("$style")
done

rc=0
for i in "${!pids[@]}"; do
  if wait "${pids[$i]}"; then
    echo "----- [$FONT_BASENAME/${names[$i]}] ok -----"
    cat "${logs[$i]}"
  else
    echo "##### [$FONT_BASENAME/${names[$i]}] FAILED #####" >&2
    cat "${logs[$i]}" >&2
    rc=1
  fi
done
[ "$rc" -eq 0 ] || { echo "==> merge FAILED for '$FAMILY'" >&2; exit 1; }
echo "==> merge complete -> $VARIANT_DIR"
