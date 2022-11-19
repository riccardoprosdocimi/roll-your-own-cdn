from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = 25016
ORIGIN_PORT = 8080
ORIGIN_SERVER = "cs5700cdnorigin.ccs.neu.edu"


class CdnHttpServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write("Hello World".encode())


if __name__ == "__main__":
    webServer = HTTPServer(("localhost", PORT), CdnHttpServer)
    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass
    webServer.server_close()
    print("server stopped")
