#!/usr/bin/env bash
# Build Kusunoki Mono — self-contained SF Mono Square reproduction + transforms.
#   P1 base    : SF Mono ×0.809 (square) + Migu 1M ×0.82
#   P2 nerd    : official nerd-fonts font-patcher --variable-width-glyphs (Propo, v3.4.0)
#   P2.5 scale : shrink icons taller than SF Mono Square to match it (same-glyph only;
#                needs a local SFMS ref, else skipped)
#   P2.6 ligs  : graft JetBrains Mono ligatures (calt), scaled to the cell width
#                and the target x-height (LIG_YSCALE) so tall ops aren't oversized
#   P3 lineseed: swap kana/kanji to LINE Seed JP; 、。 & brackets by LINE Seed bearing
#   P4 italic  : graft GSC true-italic letters + centre (italic styles only)
#   P5 final   : name / OS2 / metrics (RIBBI family "Kusunoki Mono")
#
#   scripts/build.sh
#
# Deps: fontforge, uv (fonttools), and sources/nerd-patcher (official FontPatcher).
# Knobs (env): JP_SCALE (Migu size, 0.82), ITALIC_INK_OFFSET (0=centred),
# LIG_YSCALE (ligature vertical scale, 1.478), GSC_R/GSC_B (GSC italic weight), KM_VERSION,
# KM_SFMS_DIR (dir with SFMonoSquare-*.otf for P2.5; default ~/Library/Fonts),
# KM_AMBIGUOUS_WIDTH (narrow[default]=ambiguous symbols like ※ are 1 cell / wide=2 cells).
set -uo pipefail
cd "$(dirname "$0")/.."
ROOT="$PWD"
SRC=sources
B=build/sfms
BASE="$B/base"; NERDDIR="$B/nerd"; LIGDIR="$B/lig"; STAGE="$B/stage"; DIST="dist"
mkdir -p "$BASE" "$NERDDIR" "$LIGDIR" "$STAGE" "$DIST"

export JP_SCALE="${JP_SCALE:-0.82}"
export ITALIC_INK_OFFSET="${ITALIC_INK_OFFSET:-0.0}"
export LIG_YSCALE="${LIG_YSCALE:-1.478}"
GSC_R="${GSC_R:-360}"; GSC_B="${GSC_B:-650}"
PATCHER_DIR="$ROOT/$SRC/nerd-patcher"
GSC_IT="$ROOT/$SRC/google-sans-code/GoogleSansCode-Italic[wght].ttf"
KM_SFMS_DIR="${KM_SFMS_DIR:-$HOME/Library/Fonts}"   # SFMS ref for P2.5 (optional)
SFMS_REF="$KM_SFMS_DIR/SFMonoSquare-Regular.otf"    # one ref reused for all weights
ICONPLAN="$B/iconscale.json"                        # built once from Regular, reused

JB_VF="$ROOT/$SRC/jetbrains-mono/JetBrainsMono[wght].ttf"
JB_R="$LIGDIR/JetBrainsMono-Regular.ttf"
JB_B="$LIGDIR/JetBrainsMono-Bold.ttf"
echo "==> instancing JetBrains Mono (wght 400 / 700) for ligatures"
uv run scripts/instance_vf.py "$JB_VF" "$JB_R" 400 >/dev/null
uv run scripts/instance_vf.py "$JB_VF" "$JB_B" 700 >/dev/null

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

icon_scale() {  # $1=style $2=patched.otf ; echoes path to use downstream (scaled, or original)
  local st=$1 patched=$2
  [ -f "$SFMS_REF" ] || { echo "$patched"; return 0; }   # no SFMS ref -> skip P2.5
  if [ ! -f "$ICONPLAN" ]; then                          # plan once (from Regular), reuse
    uv run scripts/plan_icon_scale.py "$patched" "$SFMS_REF" "$ICONPLAN" 2 0.6 \
      >"$B/iconscale.log" 2>&1 || { echo "$patched"; return 0; }
  fi
  local scaled="$NERDDIR/scaled-$st.otf"
  fontforge -quiet -script scripts/apply_icon_scale.py "$patched" "$ICONPLAN" "$scaled" \
    >>"$B/iconscale.log" 2>&1 && echo "$scaled" || echo "$patched"
}

buildone() {  # 1=style 2=sf 3=migu 4=lineseed 5=jb_instance 6=gsc_wght(optional, italics)
  local st=$1 sf=$2 migu=$3 ls=$4 jb=$5 gscw=${6:-}
  echo "==== $st ===="
  echo "-- P1 base (SF Mono + Migu)"
  fontforge -quiet -script scripts/build_base.py \
    "$ROOT/$SRC/$sf" "$ROOT/$SRC/$migu" "$ROOT/$BASE/KusunokiMono-$st.otf" "$st" >"$B/$st.p1.log" 2>&1 \
    && grep -E '^\[build_base\]' "$B/$st.p1.log" | tail -1 || { echo "  !! P1 $st FAILED"; tail -3 "$B/$st.p1.log"; return 1; }
  echo "-- P2 nerd (--variable-width-glyphs / Propo, official v3.4.0)"
  local patched; patched=$(nerd_patch "$st")
  [ -s "$patched" ] || { echo "  !! P2 $st FAILED"; tail -3 "$B/$st.p2.log"; return 1; }
  echo "   -> $(basename "$patched")"
  echo "-- P2.5 icon downscale (match SF Mono Square; same-glyph only)"
  patched=$(icon_scale "$st" "$patched")
  grep -E '\[plan_icon_scale\]|\[apply_icon_scale\]' "$B/iconscale.log" 2>/dev/null | tail -2 \
    || echo "   (skipped: no SFMS ref at $SFMS_REF)"
  echo "-- P2.6 ligatures (JetBrains, sy=LIG_YSCALE)"
  fontforge -quiet -script scripts/add_ligatures.py "$patched" "$jb" "$LIGDIR/KusunokiMono-$st.otf" >"$B/$st.plig.log" 2>&1 \
    && grep -E '^\[add_ligatures\]' "$B/$st.plig.log" | tail -1 || { echo "  !! ligatures $st FAILED"; tail -3 "$B/$st.plig.log"; return 1; }
  echo "-- P3 LINE Seed swap"
  uv run scripts/swap_lineseed.py "$LIGDIR/KusunokiMono-$st.otf" "$STAGE/KusunokiMono-$st.otf" "$ROOT/$SRC/$ls" "$st" >"$B/$st.p3.log" 2>&1 \
    && grep -E 'replaced' "$B/$st.p3.log" | tail -1 || { echo "  !! P3 $st FAILED"; tail -3 "$B/$st.p3.log"; return 1; }
  if [ -n "$gscw" ]; then
    echo "-- P4 GSC italic graft + centre"
    uv run scripts/graft_italic.py "$STAGE/KusunokiMono-$st.otf" "$GSC_IT" "$B/$st.graft.otf" "$gscw" >"$B/$st.p4.log" 2>&1 \
      && uv run scripts/center_italic.py "$B/$st.graft.otf" "$STAGE/KusunokiMono-$st.otf" >>"$B/$st.p4.log" 2>&1 \
      && grep -E '\[graft_italic\]|\[center_italic\]' "$B/$st.p4.log" | tail -2 || { echo "  !! P4 $st FAILED"; tail -3 "$B/$st.p4.log"; return 1; }
  fi
  echo "-- P5 finalize"
  uv run scripts/finalize.py "$STAGE/KusunokiMono-$st.otf" "$DIST/KusunokiMono-$st.otf" "$st" >"$B/$st.p5.log" 2>&1 \
    && grep -E '\[finalize\]' "$B/$st.p5.log" | tail -1 || { echo "  !! P5 $st FAILED"; tail -3 "$B/$st.p5.log"; return 1; }
}

buildone Regular    sf-mono/SF-Mono-Regular.otf       migu-1m/migu-1m-regular.ttf  lineseed-jp/LINESeedJP-Regular.ttf "$JB_R"
buildone Bold       sf-mono/SF-Mono-Bold.otf          migu-1m/migu-1m-bold.ttf     lineseed-jp/LINESeedJP-Bold.ttf   "$JB_B"
buildone Italic     sf-mono/SF-Mono-RegularItalic.otf migu-1m/migu-1m-regular.ttf  lineseed-jp/LINESeedJP-Regular.ttf "$JB_R" "$GSC_R"
buildone BoldItalic sf-mono/SF-Mono-BoldItalic.otf    migu-1m/migu-1m-bold.ttf     lineseed-jp/LINESeedJP-Bold.ttf   "$JB_B" "$GSC_B"

echo "==== built ===="
ls -1 "$DIST"/KusunokiMono-*.otf