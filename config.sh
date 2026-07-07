#!/usr/bin/env bash
# Kusunoki Mono — merge-side build configuration (single source of truth).
#
# The Iosevka-side design (variants / cv## / ligations / exportGlyphNames) lives
# in private-build-plans.toml. This file holds everything the *merge* stage needs.
#
# Sourced by scripts/*.sh; the Python scripts (merge.py / fix.py / specimen.py)
# read these values as environment variables. NERD_FONTS and LIGATURES may be
# overridden from the environment to build the four release variants.

set -a  # auto-export every variable defined below (so child processes inherit)

# --- Identity -------------------------------------------------------------
FAMILY_BASE="Kusunoki Mono"
VERSION="0.3.0"
BUILD_PLAN="KusunokiMono"          # Iosevka plan name in private-build-plans.toml (one base build)

# --- Variant axes (override via env; both default on) ----------------------
NERD_FONTS="${NERD_FONTS:-1}"      # 1 = merge Nerd Fonts icon glyphs
LIGATURES="${LIGATURES:-1}"        # 1 = keep Iosevka's default (calt) ligatures

# --- Derived family + basename. Additive tokens on a bare base: the base has
#     neither feature; "NF" adds Nerd Fonts, "LG" adds ligatures, both -> "NFLG".
#     Four variants install side by side. -----------------------------------
_token=""
[ "$NERD_FONTS" = "1" ] && _token="${_token}NF"
[ "$LIGATURES" = "1" ] && _token="${_token}LG"
if [ -n "$_token" ]; then FAMILY="${FAMILY_BASE} ${_token}"; else FAMILY="$FAMILY_BASE"; fi
FONT_BASENAME="${FAMILY// /}"      # KusunokiMono / KusunokiMonoNF / KusunokiMonoLG / KusunokiMonoNFLG

# --- Cell width / density (the main knob) ---------------------------------
# 0.6 : respect the gist's Normal(600). Full-width CJK advance = 1.2em.
# 0.5 : conventional / dense. Full-width CJK = 1.0em exactly; uses Condensed(500).
WIDTH_EM="${WIDTH_EM:-0.6}"

# --- Em unit --------------------------------------------------------------
# Kept at 1000 so Iosevka is used verbatim (native UPM): outlines, hinting and
# ligature GSUB pass through untouched. Only BIZ UDGothic + Nerd are rescaled.
TARGET_EM="1000"

# --- Italic ---------------------------------------------------------------
ITALIC_ANGLE="9.4"                 # must match slopes.Italic.angle in the toml

# --- Styles (must exist as Iosevka outputs; override via env for quick tests) --
STYLES="${STYLES:-Regular Bold Italic BoldItalic}"

# --- Toggles --------------------------------------------------------------
VISUALIZE_ZENKAKU_SPACE="1"        # draw a visible glyph for the ideographic space U+3000

# --- Vertical harmony tuning (inspect the specimen; tweak if CJK sits high/low)
CJK_Y_SCALE="1.0"                  # extra vertical scale applied to BIZ glyphs
CJK_Y_SHIFT="0"                    # vertical shift, in font units at TARGET_EM

# --- Derived: which Iosevka width variant feeds the chosen WIDTH_EM --------
case "$WIDTH_EM" in
  0.6) IOSEVKA_WIDTH="Normal" ;;
  0.5) IOSEVKA_WIDTH="Condensed" ;;
  *) echo "config.sh: unsupported WIDTH_EM='$WIDTH_EM' (the toml defines only 500/600)" >&2
     return 1 2>/dev/null || exit 1 ;;
esac

# --- Paths ----------------------------------------------------------------
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IOSEVKA_DIR="${IOSEVKA_DIR:-$ROOT_DIR/../Iosevka}"
SOURCES_DIR="$ROOT_DIR/sources"
BUILD_DIR="$ROOT_DIR/build"        # intermediate per-style TTFs
DIST_DIR="$ROOT_DIR/dist"          # final output root
VARIANT_DIR="$DIST_DIR/$FONT_BASENAME"   # this variant's TTFs + specimen

set +a

# Iosevka output filename for a given style at the current width.
# Default width (Normal) omits the width token; other widths prefix it.
iosevka_file() {
  local style="$1"
  if [ "$IOSEVKA_WIDTH" = "Normal" ]; then
    echo "${BUILD_PLAN}-${style}.ttf"
  elif [ "$style" = "Regular" ]; then
    echo "${BUILD_PLAN}-${IOSEVKA_WIDTH}.ttf"
  else
    echo "${BUILD_PLAN}-${IOSEVKA_WIDTH}${style}.ttf"
  fi
}
export -f iosevka_file 2>/dev/null || true
