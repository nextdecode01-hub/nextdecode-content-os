import http.server, socketserver, os, json, requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv('/home/demon/shorts_studio/.env')
CLIENT_ID = os.getenv('YOUTUBE_CLIENT_ID')
CLIENT_SECRET = os.getenv('YOUTUBE_CLIENT_SECRET')

# We know Google Cloud has: http://localhost:5678/rest/oauth2-credential/callback
# Let's write a python script that can accept the code from user or parse it!
print("CLIENT_ID:", CLIENT_ID)
