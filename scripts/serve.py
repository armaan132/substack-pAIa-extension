import http.server
import socketserver
from pathlib import Path

# Get the data directory
DATA_DIR = Path(__file__).parent.parent / "data"
PORT = 8000

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DATA_DIR), **kwargs)

if __name__ == "__main__":
    print(f"Serving files from {DATA_DIR}")
    print(f"Open http://localhost:{PORT}/index.html in your browser")
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        httpd.serve_forever() 