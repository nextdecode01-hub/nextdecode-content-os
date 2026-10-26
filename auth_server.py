import http.server
import socketserver
import urllib.parse
import os
import requests
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv("/home/demon/shorts_studio/.env")
CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID")
CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET")
TOKEN_FILE = Path("/home/demon/shorts_studio/youtube_token.json")

PORT = 5000

class OAuthHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(parsed.query)
        if "code" in qs:
            code = qs["code"][0]
            # Exchange code for token
            token_url = "https://oauth2.googleapis.com/token"
            data = {
                "code": code,
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "redirect_uri": f"http://localhost:{PORT}/callback",
                "grant_type": "authorization_code"
            }
            r = requests.post(token_url, data=data)
            tokens = r.json()
            if "access_token" in tokens:
                with open(TOKEN_FILE, "w") as f:
                    json.dump(tokens, f, indent=2)
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(b"<h1>SUCCESS! YouTube Connected! You can close this window now.</h1>")
                print("TOKEN_SAVED_SUCCESSFULLY")
                os._exit(0)
            else:
                self.send_response(400)
                self.wfile.write(f"Error: {tokens}".encode())
        else:
            self.send_response(404)
            self.end_headers()

with socketserver.TCPServer(("", PORT), OAuthHandler) as httpd:
    print(f"Auth server running on http://localhost:{PORT}")
    httpd.serve_forever()
