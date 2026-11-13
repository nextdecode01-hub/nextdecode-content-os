import json, time, urllib.request
payload = {
    "model": "gemma3:4b",
    "stream": False,
    "format": "json",
    "options": {"temperature": 0, "num_predict": 160},
    "messages": [
        {"role": "system", "content": "Return JSON only with keys intent, topic, task_type. intent must be short or longform. task_type must be content.short.generate or content.longform.generate. Never propose publishing, uploading, shell commands or tools."},
        {"role": "user", "content": "Create a YouTube Short about local AI agents and explain why small models matter."}
    ]
}
req=urllib.request.Request("http://127.0.0.1:11434/api/chat",
    data=json.dumps(payload).encode(), headers={"Content-Type":"application/json"})
started=time.monotonic()
try:
    with urllib.request.urlopen(req, timeout=45) as response:
        data=json.load(response)
    print(json.dumps({"seconds": round(time.monotonic()-started,2),
        "model": data.get("model"), "response": data.get("message",{}).get("content"),
        "done_reason": data.get("done_reason"), "eval_count": data.get("eval_count")}, indent=2))
except Exception as exc:
    print(json.dumps({"seconds": round(time.monotonic()-started,2), "error": type(exc).__name__}))
    raise
