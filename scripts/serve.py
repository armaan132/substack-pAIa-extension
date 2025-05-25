import http.server
import socketserver
from pathlib import Path

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PORT = 8000

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Serve from project root instead of data dir
        super().__init__(*args, directory=str(PROJECT_ROOT), **kwargs)

if __name__ == "__main__":
    print(f"Serving files from {PROJECT_ROOT}")
    print(f"Data directory is at {DATA_DIR}")
    print(f"Open http://localhost:{PORT}/data/index.html in your browser")
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        httpd.serve_forever() 