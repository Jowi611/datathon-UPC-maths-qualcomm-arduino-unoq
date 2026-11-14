#!/usr/bin/env python3
"""Cangur Tutor: the web page and its API, served by the board.

    python3 tutor_server.py                        # data/tutor.db, port 8090
    python3 tutor_server.py --host 0.0.0.0         # open it to the network
    python3 tutor_server.py --db data/tutor_synth.db --no-model   # on a laptop, without the model

Open http://127.0.0.1:8090 on the board. From a laptop over USB, with Wi-Fi off:

    adb forward tcp:8090 tcp:8090

Standard library only, for a laptop or for a board without App Lab. The
interface of the demo is the App Lab app in app/cangur-tutor: same page, same
routes, plus the LED matrix (board/install_app.sh sets it up).
"""
import argparse
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlparse

from copilot.tutor import settings as S
from copilot.tutor.service import Tutor, TutorError

WEB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tutor_web")
TUTOR = None


def api(path):
    """/api/<action>/<arg>/...: the same routes as the App Lab app (app/cangur-tutor). Every answer is JSON."""
    parts = [unquote(p) for p in path.strip("/").split("/")[1:]]
    action, args = (parts[0], parts[1:]) if parts else ("", [])
    if action == "start" and len(args) == 2:
        return TUTOR.start(args[0], args[1])
    if action in ("next", "profile") and len(args) == 1:
        return getattr(TUTOR, action)(int(args[0]))
    if action in ("hint", "status") and len(args) == 1:
        return getattr(TUTOR, action)(int(args[0]))
    if action in ("answer", "discard") and len(args) == 2:
        return getattr(TUTOR, action)(int(args[0]), args[1])
    if action == "matrix":
        return {"rows": 8, "cols": 13, "frame": TUTOR.frame()}
    if action == "health":
        return {"status": "ok", "language": TUTOR.language, "topics": TUTOR.available}
    return None


class Handler(BaseHTTPRequestHandler):
    def send(self, code, body, content_type):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, payload, code=200):
        self.send(code, json.dumps(payload, ensure_ascii=False).encode(), "application/json; charset=utf-8")

    def do_GET(self):
        url = urlparse(self.path)
        try:
            if url.path.startswith("/api/"):
                result = api(url.path)
                if result is None:
                    return self.send_json({"error": "No such route"}, 404)
                return self.send_json(result)
            if url.path in ("/", "/index.html"):
                with open(os.path.join(WEB, "index.html"), "rb") as f:
                    return self.send(200, f.read(), "text/html; charset=utf-8")
            if url.path.startswith("/img/"):
                image = TUTOR.image_path(url.path[len("/img/"):])
                if image:
                    with open(image, "rb") as f:
                        return self.send(200, f.read(), "image/png")
            self.send_json({"error": "Not found"}, 404)
        except TutorError as error:
            self.send_json({"error": str(error)}, 400)
        except (KeyError, ValueError):
            self.send_json({"error": "Falta un paràmetre o no és vàlid."}, 400)

    def log_message(self, *_args):
        pass  # the matrix app polls several times a second: keep the terminal quiet


def main():
    global TUTOR
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--db", default=S.DB_PATH)
    p.add_argument("--images", default=S.IMAGES_DIR)
    p.add_argument("--language", default=S.LANGUAGE, help="language of the problems shown, e.g. cat or eng")
    p.add_argument("--host", default="127.0.0.1", help="use 0.0.0.0 to open it to your network")
    p.add_argument("--port", type=int, default=S.PORT)
    p.add_argument("--no-model", action="store_true", help="never call the language model")
    args = p.parse_args()

    if not os.path.exists(args.db):
        sys.exit(f"{args.db} doesn't exist. Build it first: python3 tutor_build.py all")
    try:
        TUTOR = Tutor(args.db, images_dir=args.images, language=args.language, live_hints=not args.no_model)
    except TutorError as error:
        sys.exit(str(error))
    print(f"Problems in '{TUTOR.language}', {len(TUTOR.available)} topics: {', '.join(TUTOR.available)}")
    print(f"Model hints: {'off' if args.no_model else 'on, checked in code before they are shown'}")
    print(f"Open http://127.0.0.1:{args.port} (Ctrl+C to stop)")
    try:
        ThreadingHTTPServer((args.host, args.port), Handler).serve_forever()
    except KeyboardInterrupt:
        print()


if __name__ == "__main__":
    main()
