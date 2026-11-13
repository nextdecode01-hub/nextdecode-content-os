import sys, os, requests, json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv('/home/demon/shorts_studio/.env')
CLIENT_ID = os.getenv('YOUTUBE_CLIENT_ID')
CLIENT_SECRET = os.getenv('YOUTUBE_CLIENT_SECRET')
REDIRECT_URI = "http://localhost:5678/rest/oauth2-credential/callback"

def save_code(code_str):
    code = code_str.strip()
    if "code=" in code:
        code = code.split("code=")[1].split("&")[0]
    
    # decode percent encoding if any
    import urllib.parse
    code = urllib.parse.unquote(code)
    
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code"
    }
    r = requests.post(token_url, data=data)
    res = r.json()
    if "access_token" in res:
        token_file = Path('/home/demon/shorts_studio/youtube_token.json')
        token_file.write_text(json.dumps(res, indent=2))
        print("TOKEN_SAVED_SUCCESS")
        return True
    else:
        print("ERROR_RESPONSE:", res)
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        save_code(sys.argv[1])
    else:
        print("Usage: python3 get_code.py <code>")
