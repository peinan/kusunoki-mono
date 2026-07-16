# /// script
# requires-python = ">=3.11"
# dependencies = ["fonttools>=4.50", "skia-pathops>=0.8"]
# ///
"""Visual per-kana tuner for the P2.8 dakuten enlargement (issue #6).

    uv run scripts/dakuten_tuner.py [lineseed.ttf] [port]

Serves a local editor (default http://localhost:8765) that lists every voiced
kana and lets each one's mark be tuned: size and skip-ink gap with sliders,
position by dragging. Saving writes scripts/dakuten_overrides.json (or
KM_DAKUTEN_OVERRIDES) — the same file scripts/enlarge_dakuten.py applies at
build time, so the preview here is exactly what P2.8 produces. Run from the
repo root, then rebuild (make build, or P2.8→P3→P5) to see it in the font.
"""
import json
import os
import sys
import unicodedata
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from fontTools.pens.svgPathPen import SVGPathPen

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import enlarge_dakuten as ed

FONT = sys.argv[1] if len(sys.argv) > 1 else "sources/lineseed-jp/LINESeedJP-Regular.ttf"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 8765
HTML = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dakuten_tuner.html")


def svg_d(path):
    pen = SVGPathPen(None)
    path.draw(pen)
    return pen.getCommands()


def build_data():
    font = ed.DakutenFont(FONT)
    kana, fell_back, skipped, repaired = font.recover()
    items = []
    for ch, d in kana.items():
        items.append({
            "char": ch,
            "base": unicodedata.normalize("NFD", ch)[0],
            "gname": d["gname"],
            "is_semi": d["is_semi"],
            "fallback": d["fallback"],
            "adv": font.hmtx[d["gname"]][0],
            "body": svg_d(d["body"]),
            "mark": svg_d(d["mark"]),
            "mb": list(d["mb"]),
        })
    return {
        "font": FONT,
        "upm": font.upm,
        "skip_ink": ed.SKIP_INK,
        "defaults": {
            "dakuten": {"scale": ed.SCALE_DAKUTEN, "halo": ed.HALO_DAKUTEN},
            "handakuten": {"scale": ed.SCALE_HANDAKUTEN, "halo": ed.HALO_HANDAKUTEN},
        },
        "overrides_path": ed.OVERRIDES_PATH,
        "overrides": ed.load_overrides(),
        "notes": {"fell_back": fell_back, "skipped": skipped, "repaired": repaired},
        "kana": items,
    }


DATA = build_data()


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            with open(HTML, "rb") as f:
                self._send(200, f.read(), "text/html; charset=utf-8")
        elif self.path == "/data":
            self._send(200, json.dumps(DATA, ensure_ascii=False).encode(),
                       "application/json; charset=utf-8")
        else:
            self._send(404, b"not found", "text/plain")

    def do_POST(self):
        if self.path != "/save":
            self._send(404, b"not found", "text/plain")
            return
        n = int(self.headers.get("Content-Length", "0"))
        try:
            overrides = json.loads(self.rfile.read(n).decode("utf-8"))
            assert isinstance(overrides, dict)
        except Exception as e:  # malformed client payload — report, don't crash
            self._send(400, f"bad payload: {e}".encode(), "text/plain")
            return
        overrides = dict(sorted(overrides.items(), key=lambda kv: ord(kv[0][0])))
        with open(ed.OVERRIDES_PATH, "w", encoding="utf-8") as f:
            json.dump(overrides, f, ensure_ascii=False, indent=2)
            f.write("\n")
        DATA["overrides"] = overrides
        self._send(200, json.dumps({"ok": True, "count": len(overrides),
                                    "path": ed.OVERRIDES_PATH}).encode(),
                   "application/json")

    def log_message(self, fmt, *args):  # keep the terminal quiet
        pass


if __name__ == "__main__":
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"[dakuten_tuner] {len(DATA['kana'])} kana from {FONT}")
    print(f"[dakuten_tuner] overrides file: {ed.OVERRIDES_PATH}")
    print(f"[dakuten_tuner] open http://localhost:{PORT}")
    srv.serve_forever()
