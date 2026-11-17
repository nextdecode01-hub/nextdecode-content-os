#!/bin/bash
for port in 8765 5173 8080; do
  code=$(curl -s -m 5 -o /dev/null -w '%{http_code}' "http://127.0.0.1:${port}/health" 2>/dev/null)
  echo "port ${port} /health -> ${code}"
done