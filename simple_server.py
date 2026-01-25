import http.server
import socketserver
from http.server import SimpleHTTPRequestHandler
import os

class CORSRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

# 在当前目录下启动服务器，端口 8000
os.chdir(os.path.dirname(__file__))
with socketserver.TCPServer(("", 8000), CORSRequestHandler) as httpd:
    print("Screencast Viewer 服务器已启动")
    print("请在浏览器中访问: http://localhost:8000/screencast_viewer.html")
    print("按 Ctrl+C 停止服务器")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n服务器已停止")