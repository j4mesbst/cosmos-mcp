"""HTTP adapter for the bundled Python MCP. Bind to loopback behind an HTTPS tunnel."""
import argparse
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hmac
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
from threading import Lock
import time

SERVER = Path(__file__).resolve().parents[1] / "skills/get-started/scripts/server.py"
SESSIONS = {}
LOCK = Lock()
POOL = ThreadPoolExecutor(max_workers=4)
TOKEN = os.environ.get("COSMOS_ORIGIN_TOKEN", "")


class Session:
    def __init__(self):
        self.proc = subprocess.Popen([sys.executable, "-B", str(SERVER)],
                                     stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        self.lock = Lock()
        self.touched = time.monotonic()

    def forward(self, message):
        with self.lock:
            self.touched = time.monotonic()
            self.proc.stdin.write(json.dumps(message) + "\n")
            self.proc.stdin.flush()
            if "id" in message:
                line = self.proc.stdout.readline()
                if not line:
                    raise EOFError
                return line.encode()
            return None


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def send(self, status, body=b"", sid=None):
        self.send_response(status)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        if body:
            self.send_header("Content-Type", "application/json")
        if sid:
            self.send_header("Mcp-Session-Id", sid)
        self.end_headers()
        if body:
            self.wfile.write(body)

    def authorized(self):
        if self.path != "/mcp":
            self.send(404)
            return False
        if not hmac.compare_digest(self.headers.get("Authorization", "").encode(), ("Bearer " + TOKEN).encode()):
            self.send(401)
            return False
        return True

    def do_GET(self):
        if self.path == "/healthz":
            self.send(200, b'{"status":"ok"}')
            return
        if self.authorized():
            self.send(405)

    def do_DELETE(self):
        if not self.authorized():
            return
        with LOCK:
            session = SESSIONS.pop(self.headers.get("Mcp-Session-Id"), None)
        if session:
            session.proc.kill()
            session.proc.wait()
        self.send(204 if session else 404)

    def do_POST(self):
        if not self.authorized():
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 2_000_000:
                return self.send(413)
            message = json.loads(self.rfile.read(length))
            if not isinstance(message, dict) or message.get("jsonrpc") != "2.0" or not isinstance(message.get("method"), str):
                return self.send(400)
        except (ValueError, UnicodeError):
            return self.send(400)

        sid = self.headers.get("Mcp-Session-Id")
        with LOCK:
            for expired, session in list(SESSIONS.items()):
                if time.monotonic() - session.touched > 1800:
                    session.proc.kill()
                    session.proc.wait()
                    del SESSIONS[expired]
            if message["method"] == "initialize" and sid is None and "id" in message:
                if len(SESSIONS) >= 4:
                    return self.send(429)
                sid = secrets.token_urlsafe(24)
                SESSIONS[sid] = Session()
            session = SESSIONS.get(sid)
        if session is None:
            return self.send(404)
        try:
            body = POOL.submit(session.forward, message).result(timeout=105)
        except (OSError, EOFError, TimeoutError):
            with LOCK:
                SESSIONS.pop(sid, None)
            session.proc.kill()
            session.proc.wait()
            return self.send(502)
        self.send(200 if body else 202, body or b"", sid)


if __name__ == "__main__":
    if len(TOKEN) < 24:
        sys.exit("Set COSMOS_ORIGIN_TOKEN to a strong secret.")
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1", choices=("127.0.0.1", "0.0.0.0"))
    parser.add_argument("--port", type=int, default=os.environ.get("PORT", 8765))
    args = parser.parse_args()
    with ThreadingHTTPServer((args.host, args.port), Handler) as http:
        try:
            http.serve_forever()
        finally:
            for session in SESSIONS.values():
                session.proc.kill()
                session.proc.wait()
