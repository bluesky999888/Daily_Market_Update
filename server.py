#!/usr/bin/env python3
"""
server.py
Local HTTP server for Daily Market Summary PWA.
Serves public/ assets with correct PWA MIME types and provides an /api/update endpoint.
"""

import http.server
import json
import mimetypes
import os
import socketserver
import sys
import threading
from datetime import datetime

import update

PORT = int(os.environ.get("PORT", 8080))
PUBLIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "public")

# Ensure proper MIME types for PWA
mimetypes.add_type("application/manifest+json", ".json")
mimetypes.add_type("text/javascript", ".js")
mimetypes.add_type("image/png", ".png")


class PWAHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=PUBLIC_DIR, **kwargs)

    def end_headers(self):
        # Prevent aggressive browser caching of data files for real-time updates
        if self.path.endswith("market.json") or self.path.endswith("commentary.json"):
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
        elif self.path.endswith("sw.js"):
            self.send_header("Cache-Control", "no-cache, max-age=0")
        super().end_headers()

    def do_GET(self):
        if self.path == "/api/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()

            market_file = os.path.join(PUBLIC_DIR, "market.json")
            commentary_file = os.path.join(PUBLIC_DIR, "commentary.json")

            status = {
                "market_exists": os.path.exists(market_file),
                "market_mtime": datetime.fromtimestamp(os.path.getmtime(market_file)).isoformat() if os.path.exists(market_file) else None,
                "commentary_exists": os.path.exists(commentary_file),
                "commentary_mtime": datetime.fromtimestamp(os.path.getmtime(commentary_file)).isoformat() if os.path.exists(commentary_file) else None,
            }
            self.wfile.write(json.dumps(status, indent=2).encode("utf-8"))
            return

        if self.path == "/api/update":
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Received trigger request on /api/update")
            try:
                update.run_pipeline()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "message": "Updated successfully"}).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        super().do_GET()

    def do_POST(self):
        if self.path == "/api/update":
            self.do_GET()
            return
        self.send_error(404, "Endpoint not found")


class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


def run_server(port=PORT):
    with ReusableTCPServer(("", port), PWAHandler) as httpd:
        print("=" * 65)
        print(f" Daily Market Summary PWA Server running at:")
        print(f"   Local:   http://localhost:{port}")
        print(f"   API:     http://localhost:{port}/api/update (trigger update)")
        print(f"   Status:  http://localhost:{port}/api/status")
        print("=" * 65)
        print("Press Ctrl+C to stop the server.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")


if __name__ == "__main__":
    port_arg = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    run_server(port_arg)
