"""Local stand-in for the Gemini image API: answers any POST with a
Gemini-shaped response whose inlineData is the fixture grid PNG. No key, no net.
"""
import base64
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from tests.fixtures import make_grid_png


class _Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        self.rfile.read(length)
        data = base64.b64encode(make_grid_png()).decode()
        body = json.dumps(
            {"candidates": [{"content": {"parts": [{"inlineData": {"mimeType": "image/png", "data": data}}]}}]}
        ).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


def start():
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}/v1beta/models"
