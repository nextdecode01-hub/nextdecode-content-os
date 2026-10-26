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

REDIRECT_URI = "http://localhost:5678/rest/oauth2-credential/callback"

def get_auth_url():
    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": "https://www.googleapis.com/auth/youtube.upload",
        "prompt": "consent",
        "access_type": "offline"
    }
    return "https://accounts.google.com/o/oauth2/auth?" + urllib.parse.urlencode(params)

print("AUTH_LINK:", get_auth_url())
