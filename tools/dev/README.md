# Developer tools

- ollama_chat.py is an optional interactive client for a locally running Ollama server.
- It is not part of generation, publishing, scheduling or runtime startup.
- It uses OLLAMA_BASE_URL (default http://127.0.0.1:11434) and OLLAMA_MODEL (default gemma3:4b).
- Run it manually only when local Ollama is intentionally available. Do not call it from production pipelines.
