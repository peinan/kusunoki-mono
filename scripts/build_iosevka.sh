#!/usr/bin/env bash
# Build the custom Iosevka (Latin/ASCII/ligatures base) and collect the TTFs
# for the currently-selected width into build/iosevka/.
set -euo pipefail
cd "$(dirname "$0")/.."
source ./config.sh

echo "==> Placing private-build-plans.toml into $IOSEVKA_DIR"
cp ./private-build-plans.toml "$IOSEVKA_DIR/private-build-plans.toml"

echo "==> Building Iosevka plan '$BUILD_PLAN' (this takes a while)"
jcmd_arg=""
[ -n "${IOSEVKA_JCMD:-}" ] && jcmd_arg="--jCmd=$IOSEVKA_JCMD"   # cap parallelism (CI memory)
( cd "$IOSEVKA_DIR" && npm run build -- "ttf::$BUILD_PLAN" $jcmd_arg )

ttf_dir="$IOSEVKA_DIR/dist/$BUILD_PLAN/TTF"
[ -d "$ttf_dir" ] || { echo "ERROR: $ttf_dir not found after build" >&2; exit 1; }

# Map a style name to the Iosevka output filename for the selected width.
# The default width (Normal, width class 5) omits the width token; other widths
# prefix it to the style. (Condensed naming is verified empirically on first use.)
style_to_file() {
  local style="$1"
  if [ "$IOSEVKA_WIDTH" = "Normal" ]; then
    echo "${BUILD_PLAN}-${style}.ttf"
  elif [ "$style" = "Regular" ]; then
    echo "${BUILD_PLAN}-${IOSEVKA_WIDTH}.ttf"
  else
    echo "${BUILD_PLAN}-${IOSEVKA_WIDTH}${style}.ttf"
  fi
}

echo "==> Collecting '$IOSEVKA_WIDTH' TTFs into $BUILD_DIR/iosevka"
mkdir -p "$BUILD_DIR/iosevka"
for style in $STYLES; do
  f="$(style_to_file "$style")"
  src="$ttf_dir/$f"
  if [ ! -s "$src" ]; then
    echo "ERROR: expected '$f' not found in $ttf_dir. Contents:" >&2
    ls -1 "$ttf_dir" >&2
    exit 1
  fi
  cp "$src" "$BUILD_DIR/iosevka/$f"
  echo "    collected $f"
done

echo "==> Iosevka build complete"
