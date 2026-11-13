import json, time, urllib.request
payload = {
    "model": "gemma3:4b", "stream": False, "format": "json",
    "options": {"temperature": 0, "num_predict": 96},
    "messages": [
        {"role": "system", "content": "Classify the user's requested deliverable. Return exactly JSON: {\"task_type\":\"content.short.generate\"} for a short vertical video or {\"task_type\":\"content.longform.generate\"} for a long video, otherwise {\"task_type\":\"unsupported\"}. Do not choose a video type for research-only, coding, publishing, uploading, or unrelated tasks. No other keys."},
        {"role": "user", "content": "Make a vertical video about local AI agents and why small models matter."}
    ]
}
req=urllib.request.Request("http://127.0.0.1:11434/api/chat",
    data=json.dumps(payload).encode(), headers={"Content-Type":"application/json"})
started=time.monotonic()
with urllib.request.urlopen(req, timeout=30) as response:
    data=json.load(response)
print(json.dumps({"seconds":round(time.monotonic()-started,2),
    "response":data.get("message",{}).get("content"),"eval_count":data.get("eval_count")},indent=2))
