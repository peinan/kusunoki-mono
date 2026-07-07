#!/usr/bin/env bash
# Build all four release variants (Nerd Fonts on/off x ligatures on/off).
# Iosevka must already be built (run `make iosevka` first) — it is shared by all
# variants; only the merge stage differs per variant.
set -euo pipefail
cd "$(dirname "$0")/.."

[ -d build/iosevka ] || { echo "ERROR: build/iosevka missing — run 'make iosevka' first" >&2; exit 1; }

for nerd in 1 0; do
  for liga in 1 0; do
    NERD_FONTS=$nerd LIGATURES=$liga bash scripts/merge_all.sh
  done
done
echo "==> all 4 variants built under dist/"
