# /// script
# requires-python = ">=3.11"
# dependencies = ["fonttools>=4.50", "skia-pathops>=0.8"]
# ///
"""Visual per-kana tuner for the P2.8 dakuten enlargement (issue #6).

    uv run scripts/dakuten_tuner.py [port]

Serves a local editor (default http://localhost:8765) over both LINE Seed
weights. Styles: Regular / Bold / Italic / BoldItalic — italics preview the
same weight skewed, and every style inherits the Regular values until a field
is changed on its tab. Per kana: mark size, rotation, skip-ink gap (uniform +
per-side), position by dragging, and an exclude toggle. Saving writes
scripts/dakuten_overrides.json (or KM_DAKUTEN_OVERRIDES) — the same file
scripts/enlarge_dakuten.py applies at build time, through the same code path,
so the preview is exactly what P2.8 produces. Rebuild to see it in the font.
"""
import json
import os
import sys
import unicodedata
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from fontTools.pens.svgPathPen import SVGPathPen

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import enlarge_dakuten as ed

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = {w: os.path.join(REPO, "sources", "lineseed-jp", f"LINESeedJP-{w.capitalize()}.ttf")
         for w in ("regular", "bold")}
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
HTML = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dakuten_tuner.html")
ITALIC_SKEW = 10          # preview-only lean for the italic tabs, degrees


def svg_d(path):
    pen = SVGPathPen(None)
    path.draw(pen)
    return pen.getCommands()


def weight_data(path):
    font = ed.DakutenFont(path)
    kana, fell_back, skipped, repaired, rebuilt = font.recover()
    items = []
    for ch, d in kana.items():
        cts = ed.path_contours(d["mark"])
        if not d["is_semi"] and len(cts) == 2:
            # per-dot pieces so the client can slide them apart (spread)
            parts = [svg_d(ed.to_path([v])) for v, _ in cts]
            part_centers = [[(b[0] + b[2]) / 2, (b[1] + b[3]) / 2] for _, b in cts]
        else:
            parts = [svg_d(d["mark"])]
            part_centers = [[(d["mb"][0] + d["mb"][2]) / 2, (d["mb"][1] + d["mb"][3]) / 2]]
        items.append({
            "char": ch,
            "base": unicodedata.normalize("NFD", ch)[0],
            "gname": d["gname"],
            "is_semi": d["is_semi"],
            "fallback": d["fallback"],
            "rebuilt": d["gname"] in rebuilt or d["gname"] in repaired,
            "adv": font.hmtx[d["gname"]][0],
            "body": svg_d(d["body"]),
            "mark": svg_d(d["mark"]),
            "parts": parts,
            "part_centers": part_centers,
            "mb": list(d["mb"]),
        })
    return {"kana": items, "upm": font.upm,
            "notes": {"fell_back": fell_back, "skipped": skipped,
                      "repaired": repaired, "rebuilt": rebuilt}}


def build_data():
    weights = {w: weight_data(p) for w, p in FONTS.items()}
    return {
        "fonts": {w: os.path.relpath(p, REPO) for w, p in FONTS.items()},
        "upm": weights["regular"]["upm"],
        "skip_ink": ed.SKIP_INK,
        "italic_skew": ITALIC_SKEW,
        "defaults": {
            "dakuten": {"scale": ed.SCALE_DAKUTEN, "halo": ed.HALO_DAKUTEN},
            "handakuten": {"scale": ed.SCALE_HANDAKUTEN, "halo": ed.HALO_HANDAKUTEN},
        },
        "overrides_path": os.path.relpath(ed.OVERRIDES_PATH, REPO),
        "overrides": ed.load_overrides(),
        "weights": weights,
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
        try:
            n = int(self.headers.get("Content-Length", "0"))
            overrides = json.loads(self.rfile.read(n).decode("utf-8"))
            assert isinstance(overrides, dict), "payload must be an object"
            overrides = dict(sorted(overrides.items(), key=lambda kv: ord(kv[0][0])))
            with open(ed.OVERRIDES_PATH, "w", encoding="utf-8") as f:
                json.dump(overrides, f, ensure_ascii=False, indent=2)
                f.write("\n")
            DATA["overrides"] = overrides
            self._send(200, json.dumps({"ok": True, "count": len(overrides),
                                        "path": os.path.relpath(ed.OVERRIDES_PATH, REPO)}).encode(),
                       "application/json")
        except Exception as e:  # report to the client instead of dropping the socket
            self._send(500, f"save failed: {e}".encode(), "text/plain; charset=utf-8")

    def log_message(self, fmt, *args):  # keep the terminal quiet
        pass


if __name__ == "__main__":
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    n = len(DATA["weights"]["regular"]["kana"])
    print(f"[dakuten_tuner] {n} kana × {len(FONTS)} weights from {REPO}/sources/lineseed-jp")
    print(f"[dakuten_tuner] overrides file: {ed.OVERRIDES_PATH}")
    print(f"[dakuten_tuner] open http://localhost:{PORT}")
    srv.serve_forever()
