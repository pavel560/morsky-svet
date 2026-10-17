#!/usr/bin/env python3
"""Mořský svět — tiny local web server (stdlib only).

    python3 serve.py                 # http://0.0.0.0:8642
    python3 serve.py --port 9000
    python3 serve.py --open          # also open the default browser
    python3 serve.py --cert c.pem --key k.pem   # HTTPS (needed for offline/PWA on the iPad)

Runs on macOS (python3 >= 3.8, no packages).
"""
from __future__ import annotations

import argparse
import errno
import re
import functools
import http.server
import os
import socket
import ssl
import sys
import threading
import webbrowser

DEFAULT_PORT = 8642
HERE = os.path.dirname(os.path.abspath(__file__))

MIME_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".htm": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".mjs": "text/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".webmanifest": "application/manifest+json; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".avif": "image/avif",
    ".gif": "image/gif",
    ".ico": "image/x-icon",
    ".woff2": "font/woff2",
    ".woff": "font/woff",
    ".txt": "text/plain; charset=utf-8",
    ".md": "text/plain; charset=utf-8",
    ".mp3": "audio/mpeg",
    ".wasm": "application/wasm",
    ".wav": "audio/wav",
}

# Files that change during development: browser must revalidate every time.
NO_CACHE_EXT = {".html", ".htm", ".js", ".mjs", ".css", ".json", ".webmanifest", ".svg", ".md", ".txt"}


class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map, **MIME_TYPES}
    quiet = False

    def end_headers(self):
        path = self.path.split("?", 1)[0].split("#", 1)[0]
        ext = os.path.splitext(path)[1].lower()
        if path.endswith("/") or ext in NO_CACHE_EXT or path.endswith("sw.js"):
            self.send_header("Cache-Control", "no-cache")
        else:
            self.send_header("Cache-Control", "public, max-age=3600")
        self.send_header("Accept-Ranges", "bytes")
        super().end_headers()

    def send_head(self):
        """Single byte-range support (Safari's <audio>/<video> insist on 206 Partial Content)."""
        self._range_left = None
        rng = self.headers.get("Range")
        path = self.translate_path(self.path)
        m = re.match(r"bytes=(\d*)-(\d*)$", (rng or "").strip())
        if not m or not os.path.isfile(path) or (m.group(1) == "" and m.group(2) == ""):
            return super().send_head()
        size = os.path.getsize(path)
        if m.group(1) == "":
            start, end = max(0, size - int(m.group(2))), size - 1
        else:
            start = int(m.group(1))
            end = min(int(m.group(2)), size - 1) if m.group(2) else size - 1
        if start >= size or start > end:
            self.send_response(416)
            self.send_header("Content-Range", f"bytes */{size}")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return None
        f = open(path, "rb")
        f.seek(start)
        self.send_response(206)
        self.send_header("Content-Type", self.guess_type(path))
        self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Content-Length", str(end - start + 1))
        self.end_headers()
        self._range_left = end - start + 1
        return f

    def copyfile(self, source, outputfile):
        left = getattr(self, "_range_left", None)
        if left is None:
            return super().copyfile(source, outputfile)
        while left > 0:
            chunk = source.read(min(65536, left))
            if not chunk:
                break
            outputfile.write(chunk)
            left -= len(chunk)

    def list_directory(self, path):  # no directory listings
        self.send_error(404, "Not found")
        return None

    def log_message(self, fmt, *args):
        if not self.quiet:
            sys.stderr.write("  %s  %s\n" % (self.address_string(), fmt % args))


def lan_addresses() -> list[str]:
    """Best-effort list of this machine's IPv4 LAN addresses (no packets are sent)."""
    ips: set[str] = set()
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("10.255.255.255", 1))
            ips.add(s.getsockname()[0])
    except OSError:
        pass
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ips.add(info[4][0])
    except OSError:
        pass
    good = [ip for ip in ips if not ip.startswith(("127.", "169.254.", "0."))]
    return sorted(good, key=lambda ip: (ip.startswith("100."), ip))


def mdns_name() -> str | None:
    name = socket.gethostname().split(".")[0]
    return f"{name}.local" if name and name != "localhost" else None


def make_server(host: str, port: int, directory: str = HERE, quiet: bool = False,
                cert: str | None = None, key: str | None = None) -> http.server.ThreadingHTTPServer:
    handler = functools.partial(type("H", (Handler,), {"quiet": quiet}), directory=directory)
    # A browser opens many parallel connections (≈30 ES modules + fonts + art) over HTTP/1.0; socketserver's default
    # listen backlog of 5 drops some of them on macOS (seen in e2e: js/app.js never reached the server).
    server_cls = type("Server", (http.server.ThreadingHTTPServer,), {"allow_reuse_address": True, "request_queue_size": 128})
    httpd = server_cls((host, port), handler)
    httpd.daemon_threads = True
    if cert:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(cert, key)
        httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)
    return httpd


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Mořský svět local server")
    ap.add_argument("--port", type=int, default=int(os.environ.get("MORSKY_SVET_PORT", DEFAULT_PORT)))
    ap.add_argument("--host", default="0.0.0.0", help="bind address (default 0.0.0.0 = whole LAN)")
    ap.add_argument("--dir", default=HERE, help="folder to serve (default: this script's folder)")
    ap.add_argument("--open", action="store_true", help="open the browser after start")
    ap.add_argument("--quiet", action="store_true", help="do not log every request")
    ap.add_argument("--cert", help="TLS certificate (PEM) — enables HTTPS")
    ap.add_argument("--key", help="TLS private key (PEM)")
    args = ap.parse_args(argv)

    scheme = "https" if args.cert else "http"
    local_url = f"{scheme}://localhost:{args.port}/"
    try:
        httpd = make_server(args.host, args.port, args.dir, args.quiet, args.cert, args.key)
    except OSError as e:
        if e.errno in (errno.EADDRINUSE, 48, 98):
            print(f"Port {args.port} je obsazený — Mořský svět už nejspíš běží. Zkuste {local_url}")
            print(f"(Port {args.port} is already in use; use --port to pick another.)")
            if args.open:
                webbrowser.open(local_url)
            return 1
        raise

    print("\n  Mořský svět běží / is running\n")
    print(f"  Na tomto počítači:  {local_url}")
    for ip in lan_addresses():
        note = "   (Tailscale)" if ip.startswith("100.") else ""
        print(f"  Na iPadu (Wi-Fi):   {scheme}://{ip}:{args.port}/{note}")
    if mdns_name():
        print(f"  nebo:               {scheme}://{mdns_name()}:{args.port}/")
    print("\n  Ukončit: Ctrl+C (nebo zavřít okno Terminálu)\n")
    sys.stdout.flush()

    if args.open:
        threading.Timer(0.6, webbrowser.open, args=(local_url,)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n  Konec. Ahoj!")
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
