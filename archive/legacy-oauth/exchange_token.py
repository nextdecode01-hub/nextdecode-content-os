import sys
import requests
import json
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv("/home/demon/shorts_studio/.env")
CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID")
CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET")
REDIRECT_URI = "http://localhost:5678/rest/oauth2-credential/callback"
TOKEN_FILE = Path("/home/demon/shorts_studio/youtube_token.json")

def exchange(code_or_url):
    code = code_or_url.strip()
    if "code=" in code:
        code = code.split("code=")[1].split("&")[0]
    
    url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code"
    }
    r = requests.post(url, data=data)
    res = r.json()
    if "access_token" in res:
        with open(TOKEN_FILE, "w") as f:
            json.dump(res, f, indent=2)
        print("SUCCESS_TOKEN_SAVED")
        return True
    else:
        print("ERROR:", res)
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        exchange(sys.argv[1])
    else:
        print("Provide code")
