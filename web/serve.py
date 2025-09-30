import http.server
import socketserver
import os

PORT = 8000
# The directory containing your web files (3d.html, textures, etc.)
WEB_DIR = '.'

# In Python 3.7+ you can use the directory argument.
# For older versions, you might need to os.chdir into the directory.
class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Serving GoobCAD at http://localhost:{PORT}/3d.html")
    print("Press Ctrl+C to stop the server.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print("Server stopped.")

