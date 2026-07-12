#!/usr/bin/env bash
# Build Kusunoki Mono — self-contained SF Mono Square reproduction + transforms.
#   P1 base    : SF Mono ×0.809 (square) + Migu 1M ×0.82
#   P2 nerd    : official nerd-fonts font-patcher --variable-width-glyphs (Propo, v3.4.0)
#   P3 lineseed: swap kana/kanji to LINE Seed JP (Migu fallback)
#   P4 italic  : graft GSC true-italic letters + centre (italic styles only)
#   P5 final   : name / OS2 / metrics (RIBBI family "Kusunoki Mono")
#
#   scripts/sfmono/build.sh
#
# Deps: fontforge, uv (fonttools), and sources/nerd-patcher (official FontPatcher).
# Knobs (env): JP_SCALE (Migu size, 0.82), ITALIC_INK_OFFSET (0=centred),
# GSC_R/GSC_B (GSC italic weight), KM_VERSION.
set -uo pipefail
cd "$(dirname "$0")/../.."
ROOT="$PWD"
SRC=sources
B=build/sfms
BASE="$B/base"; NERDDIR="$B/nerd"; STAGE="$B/stage"; DIST="$B/dist"
mkdir -p "$BASE" "$NERDDIR" "$STAGE" "$DIST"

export JP_SCALE="${JP_SCALE:-0.82}"
export ITALIC_INK_OFFSET="${ITALIC_INK_OFFSET:-0.0}"
GSC_R="${GSC_R:-360}"; GSC_B="${GSC_B:-650}"
PATCHER_DIR="$ROOT/$SRC/nerd-patcher"
GSC_IT="$ROOT/$SRC/google-sans-code/GoogleSansCode-Italic[wght].ttf"

nerd_patch() {  # $1=style; logs to $B/$1.p2.log; echoes patched .otf path on stdout
  local st=$1
  rm -f "$NERDDIR"/*.otf
  # --variable-width-glyphs (Nerd Font Propo): keep each icon's natural width and
  # per-set size, like SF Mono Square. --single-width-glyphs (Mono) instead packs
  # every icon into one half-cell, shrinking non-Powerline icons to ~50% height
  # (too small — issue #9). Existing Latin/CJK advances are untouched either way.
  ( cd "$PATCHER_DIR" && fontforge -script ./font-patcher \
      --complete --variable-width-glyphs --careful --quiet \
      --outputdir "$ROOT/$NERDDIR" "$ROOT/$BASE/KusunokiMono-$st.otf" ) >"$B/$st.p2.log" 2>&1
  ls "$NERDDIR"/*.otf 2>/dev/null | head -1
}

buildone() {  # 1=style 2=sf 3=migu 4=lineseed 5=gsc_wght(optional, italics)
  local st=$1 sf=$2 migu=$3 ls=$4 gscw=${5:-}
  echo "==== $st ===="
  echo "-- P1 base (SF Mono + Migu)"
  fontforge -quiet -script scripts/sfmono/build_base.py \
    "$ROOT/$SRC/$sf" "$ROOT/$SRC/$migu" "$ROOT/$BASE/KusunokiMono-$st.otf" "$st" >"$B/$st.p1.log" 2>&1 \
    && grep -E '^\[build_base\]' "$B/$st.p1.log" | tail -1 || { echo "  !! P1 $st FAILED"; tail -3 "$B/$st.p1.log"; return 1; }
  echo "-- P2 nerd (--variable-width-glyphs / Propo, official v3.4.0)"
  local patched; patched=$(nerd_patch "$st")
  [ -s "$patched" ] || { echo "  !! P2 $st FAILED"; tail -3 "$B/$st.p2.log"; return 1; }
  echo "   -> $(basename "$patched")"
  echo "-- P3 LINE Seed swap"
  uv run scripts/sfmono/swap_lineseed.py "$patched" "$STAGE/KusunokiMono-$st.otf" "$ROOT/$SRC/$ls" "$st" >"$B/$st.p3.log" 2>&1 \
    && grep -E 'replaced' "$B/$st.p3.log" | tail -1 || { echo "  !! P3 $st FAILED"; tail -3 "$B/$st.p3.log"; return 1; }
  if [ -n "$gscw" ]; then
    echo "-- P4 GSC italic graft + centre"
    uv run scripts/sfmono/graft_italic.py "$STAGE/KusunokiMono-$st.otf" "$GSC_IT" "$B/$st.graft.otf" "$gscw" >"$B/$st.p4.log" 2>&1 \
      && uv run scripts/sfmono/center_italic.py "$B/$st.graft.otf" "$STAGE/KusunokiMono-$st.otf" >>"$B/$st.p4.log" 2>&1 \
      && grep -E '\[graft_italic\]|\[center_italic\]' "$B/$st.p4.log" | tail -2 || { echo "  !! P4 $st FAILED"; tail -3 "$B/$st.p4.log"; return 1; }
  fi
  echo "-- P5 finalize"
  uv run scripts/sfmono/finalize.py "$STAGE/KusunokiMono-$st.otf" "$DIST/KusunokiMono-$st.otf" "$st" >"$B/$st.p5.log" 2>&1 \
    && grep -E '\[finalize\]' "$B/$st.p5.log" | tail -1 || { echo "  !! P5 $st FAILED"; tail -3 "$B/$st.p5.log"; return 1; }
}

buildone Regular    sf-mono/SF-Mono-Regular.otf       migu-1m/migu-1m-regular.ttf  lineseed-jp/LINESeedJP-Regular.ttf
buildone Bold       sf-mono/SF-Mono-Bold.otf          migu-1m/migu-1m-bold.ttf     lineseed-jp/LINESeedJP-Bold.ttf
buildone Italic     sf-mono/SF-Mono-RegularItalic.otf migu-1m/migu-1m-regular.ttf  lineseed-jp/LINESeedJP-Regular.ttf "$GSC_R"
buildone BoldItalic sf-mono/SF-Mono-BoldItalic.otf    migu-1m/migu-1m-bold.ttf     lineseed-jp/LINESeedJP-Bold.ttf   "$GSC_B"

echo "==== built ===="
ls -1 "$DIST"/KusunokiMono-*.otf