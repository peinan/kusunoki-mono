#!/usr/bin/env bash
# Run metric assertions and generate dist/specimen.html, then open it (macOS).
set -euo pipefail
cd "$(dirname "$0")/.."
source ./config.sh
uv run scripts/specimen.py
[ "${OPEN_SPECIMEN:-1}" = "1" ] && command -v open >/dev/null 2>&1 && open "$DIST_DIR/specimen.html" || true
