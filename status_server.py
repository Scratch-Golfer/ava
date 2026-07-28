"""Serves status_display.html and status.json on localhost so you can open
the light indicator in a browser tab."""

import functools
import http.server
import threading


def start_status_server(directory, port=8765):
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=directory)
    server = http.server.ThreadingHTTPServer(("localhost", port), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print(f"[status] Light indicator running at http://localhost:{port}/status_display.html")
    return server
