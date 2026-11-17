# NEXTDECODE ? Local Model Removal & WSL Disk Cleanup

Date: 2026-11-16

## User decision

Local inference is not part of the NEXTDECODE production workflow because it is too slow on this workstation. The project must use approved remote/free-first providers and must not silently fall back to local inference.

## Removed

- Uninstalled the WSL Snap package ollama with purge.
- Removed all five Ollama models: qwen3-fast, coder-local, qwen3-local, qwen2.5-coder:3b, qwen3:4b.
- Removed the Ollama model store under /var/snap/ollama/common (previously 4.2 GB).
- Removed the cached Faster-Whisper base model directory from the Hugging Face cache.
- Removed disposable package/build caches: pip, uv, node-gyp, Trivy vulnerability DB cache, apt package cache and apt lists.

## Project policy changes

- .env: TTS_PROVIDER=edge_tts, TTS_ALLOW_LOCAL_MODELS=false.
- app/voice/provider.py: Kokoro local TTS is excluded from fallback routing and direct synthesis is denied unless local models are explicitly enabled.
- .env.example: documents the local-model opt-in as disabled.
- Regression tests cover the disabled local path. tests/test_voice_naturalness.py: 24 passed.
- The local Kokoro runtime code and Python dependencies were retained, but the runtime is blocked by default. No large model-weight files were found inside the project repository.

## Disk observations

- Windows C: free space before cleanup: 56.84 GB.
- Windows C: free space after cleanup: 58.36 GB (+1.52 GB observed).
- WSL root filesystem before: 59 GB used; after: 52 GB used (approximately 7 GB returned inside the distro).
- The Ubuntu WSL distro and NEXTDECODE project were preserved.
- The WSL virtual disk was approximately 60.56 GB. Host-side compaction was attempted but WSL reported that the VHD was still in use; diskpart was blocked by workstation command policy. Therefore the full internal space reclamation is not yet reflected on C:.

## Preserved intentionally

- Ubuntu WSL distribution.
- /home/demon/shorts_studio repository and its generated outputs.
- Project Python environments (venv, .venv), Node/browser automation caches and installed project dependencies.
- FFmpeg, browser automation, security tools and agent caches.

## Follow-up for full C: reclamation

Close all WSL-backed terminals, VS Code/Codex remote sessions and processes using Ubuntu, then run wsl --shutdown. After Ubuntu is fully stopped, compact the exact ext4.vhdx at:

C:\Users\yadav\AppData\Local\wsl\{83bee23e-ebd9-4522-9e25-cb26f15e64d9}\ext4.vhdx

Use an elevated Windows maintenance path supported on the machine (Hyper-V Optimize-VHD when available, otherwise DiskPart compact vdisk). Do not delete or unregister the Ubuntu distro. Recheck C: free space after compaction.
