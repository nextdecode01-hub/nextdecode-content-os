#!/usr/bin/env python3
"""Small local chat client for the Ollama model used by Nextdecode."""
from __future__ import annotations

import json
import os
import sys
from urllib.request import Request, urlopen

BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
MODEL = os.getenv("OLLAMA_MODEL", "gemma3:4b")

prompt = " ".join(sys.argv[1:]).strip()
if not prompt:
    prompt = input("You: ").strip()
if not prompt:
    raise SystemExit("Enter a message.")

payload = json.dumps({
    "model": MODEL,
    "messages": [{"role": "user", "content": prompt}],
    "stream": False,
}).encode("utf-8")
request = Request(
    f"{BASE_URL}/api/chat",
    data=payload,
    headers={"Content-Type": "application/json"},
    method="POST",
)
with urlopen(request, timeout=180) as response:
    data = json.load(response)
print(data["message"]["content"].strip())
