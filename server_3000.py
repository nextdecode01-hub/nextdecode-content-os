import http.server, socketserver, os, json, requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv('/home/demon/shorts_studio/.env')
CLIENT_ID = os.getenv('YOUTUBE_CLIENT_ID')
CLIENT_SECRET = os.getenv('YOUTUBE_CLIENT_SECRET')
PORT = 3000

class H(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if 'code=' in self.path:
            code = self.path.split('code=')[1].split('&')[0]
            token_url = 'https://oauth2.googleapis.com/token'
            data = {
                'code': code,
                'client_id': CLIENT_ID,
                'client_secret': CLIENT_SECRET,
                'redirect_uri': f'http://localhost:{PORT}',
                'grant_type': 'authorization_code'
            }
            res = requests.post(token_url, data=data).json()
            if 'access_token' in res:
                Path('/home/demon/shorts_studio/youtube_token.json').write_text(json.dumps(res, indent=2))
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b'<h1 style="color:green;font-family:sans-serif;text-align:center;margin-top:100px;">SUCCESS! Nextdecode YouTube Linked Successfully! You can close this tab now.</h1>')
                print('AUTH_TOKEN_SAVED_PERFECTLY')
                os._exit(0)
            else:
                self.send_response(400)
                self.wfile.write(str(res).encode())

with socketserver.TCPServer(("", PORT), H) as httpd:
    print(f"Server started on port {PORT}")
    httpd.serve_forever()
