# OS-Level Social Media Automation: Complete Research & Architecture Blueprint

This document consolidates the best tools from our earlier research and adds **new, deep-dive OS-level automation, anti-detection, and cross-platform publishing repositories** discovered across GitHub, Reddit (`r/LocalLLaMA`, `r/selfhosted`, `r/webscraping`), and X. It is designed specifically as an implementation blueprint for an **OS-level, zero-API-cost Social Media Automation Engine**.

---

## Part 1: Curated Tools from Earlier Research (Ready to Implement)

These are the highest-value components we already uncovered that fit directly into your social media automation stack:

### 1. Zero-Cost Scraping & Trend Intelligence
* **`Panniantong/Agent-Reach` (`twitter-cli`, `rdt-cli`, `yt-dlp`, `Jina Reader`):**
  * **Role in Project:** Gives your OS daemon free read/search access to X (Twitter), Reddit, YouTube transcripts, and web articles using local browser session cookies (`600` permissions) instead of paid APIs.
* **`firecrawl/firecrawl` & `unclecode/crawl4ai` (v0.9.5+):**
  * **Role in Project:** Converts any competitor link, news page, or documentation site into clean, structured Markdown for script and post generation.
* **`NousResearch/hermes-agent`:**
  * **Role in Project:** Provides built-in `x_search`, modular `SKILL.md` loading, and free fallback search backends to spot viral outlier threads automatically.

### 2. Zero-Cost Local Media & Asset Generation
* **`hexgrad/kokoro` (Kokoro-82M TTS):**
  * **Role in Project:** Apache-licensed, CPU-fast text-to-speech engine that generates natural 24kHz voiceovers locally without paying ElevenLabs fees or requiring a dedicated GPU.
* **`Faster-Whisper` (`int8` CPU Mode) + `FFmpeg` + `Pillow`:**
  * **Role in Project:** Extracts exact word-level timestamps, generates `.ass` dynamic pop-up subtitles, builds 1080x1920 hook cards, and renders vertical 9:16 videos locally.
* **`heygen-com/hyperframes` & `latent-spaces/brag`:**
  * **Role in Project:** Replaces broken/paid stock footage APIs (like Pexels) by rendering animated HTML/CSS/Tailwind motion graphics, charts, and code walkthroughs directly into smooth MP4 videos.
* **`debpalash/VoiceStudio`:**
  * **Role in Project:** 100% local voice cloning and multi-language video dubbing suite.

### 3. OS Daemons, Storage & Infrastructure
* **`pocketbase/pocketbase` or `DuckDB` + `SQLite`:**
  * **Role in Project:** Single-binary local database, real-time admin UI, and embedded scheduling queue that runs under 65 MB RAM.
* **Python `watchdog` + `astral-sh/uv`:**
  * **Role in Project:** Monitors OS directories (`/dropzone`, `/rendered`, `/published`) at the kernel level so dropping a file into a folder triggers an automatic processing and posting pipeline.
* **`binwiederhier/ntfy` & `henrygd/beszel`:**
  * **Role in Project:** Sends instant push notifications to your phone when a video finishes rendering or requires human approval before posting, while tracking WSL/Docker CPU and RAM health.

---

## Part 2: NEW Research — OS-Level Execution, Stealth Browsers & Auto-Posting

When building an **OS-level social media automation system**, reading data and generating videos is only half the battle. The hardest part is **executing actions (uploading reels/shorts, scheduling threads, replying, warming accounts)** without paying $100+/month for enterprise APIs or getting banned by anti-bot systems (Cloudflare, DataDome, Arkose Labs).

Here is what top engineers on GitHub and Reddit are using right now for OS-level execution:

### 1. Engine-Level Stealth Browsers (Bypassing Bot Detection)
Standard Playwright and Selenium leak `navigator.webdriver`, canvas fingerprints, and CDP (Chrome DevTools Protocol) markers that Instagram, TikTok, LinkedIn, and X flag immediately. Use these instead:

* **`daijro/camoufox` (Engine-Level Stealth Firefox):**
  * **Why it's a game-changer:** Instead of patching fingerprints in JavaScript (which platforms easily detect), Camoufox modifies the C++ Firefox engine directly. It spoofs WebGL, Canvas, AudioContext, screen resolution, OS fonts, and human cursor micro-jitters at the binary level.
  * **Best for:** Multi-account social media management, logging into TikTok/Instagram/X, and uploading media without triggering CAPTCHAs.
* **`ultrafunkamsterdam/nodriver` (Raw CDP Async Chrome):**
  * **Why it's a game-changer:** The modern successor to `undetected-chromedriver`. It speaks directly to Chrome via raw WebSockets/CDP with **zero WebDriver binary** and **zero Selenium dependency**.
  * **Best for:** High-speed, async Python browser tasks inside your native Chrome profile.
* **`Kalihi-Dev/patchright-python` (Drop-in Stealth Playwright):**
  * **Why it's a game-changer:** Patches Playwright's runtime leaks (`Runtime.enable` CDP detection) so existing Playwright scripts pass Cloudflare and DataDome checks out of the box.

### 2. OS-Level GUI & Browser Agents
When a platform changes its HTML DOM selectors, traditional scrapers break. OS-level vision and DOM agents solve this:

* **`browser-use/browser-use` (v0.13+ - 118k+ Stars):**
  * **What it does:** Connects any LLM (including local Ollama models or Gemini/Claude) to a real browser. Crucially, **you can record one successful upload/post run and replay it deterministically** with new text/video variables without calling the LLM on every single step.
  * ⚠️ **Critical Security Fix from Research:** By default, `browser-use` sets `ANONYMIZED_TELEMETRY=true`, which sends visited URLs and task instructions to PostHog. **Always set `ANONYMIZED_TELEMETRY=false` in your `.env` on day one.**
* **`bytedance/UI-TARS-desktop` & `OpenClaw` (`openclaw/openclaw`):**
  * **What it does:** True OS-level native GUI agents. Instead of relying only on browser DOMs, they take screenshots of your desktop/window, calculate `(x, y)` coordinates, move the OS mouse with human acceleration curves, and use native OS file-picker dialogs to select and upload MP4s.

### 3. Open-Source Social Media Schedulers & Agent Skills
Instead of building every platform uploader and calendar UI from scratch, plug these open-source repos into your stack:

* **`gitroomhq/postiz-app` + `gitroomhq/postiz-agent` & `postiz-n8n`:**
  * **What it does:** The leading self-hosted, open-source social media scheduling system. They recently released `postiz-agent` (a CLI & `SKILL.md` plugin for OpenClaw, Gemini CLI, and Claude) so your OS agent can schedule cross-platform posts via a single terminal command.
* **`indranilbanerjee/socialforge` (Portable `SKILL.md` Production System):**
  * **What it does:** Contains 21 portable `SKILL.md` files for brand setup, asset indexing, copy adaptation, and human-in-the-loop approval galleries before anything goes live.
* **OS Metadata Sanitizer (`FFmpeg` + `ExifTool`):**
  * **Why Reddit builders swear by it:** Social platforms hash uploaded videos (`md5` / perceptual hashes) and inspect container metadata (`Lavf` encoder tags) to shadowban automated uploads. Running an OS-level `FFmpeg` + `ExifTool` pass to strip software tags and inject realistic iPhone/Android camera EXIF metadata boosts organic reach significantly.

---

## Part 3: Master System Architecture for Your OS-Level Project

Here is how you combine these tools into a single, cohesive **OS-Level Social Media Automation Engine** running on Linux/WSL + Windows:

```text
+-----------------------------------------------------------------------------------+
| LAYER 1: ZERO-COST INGESTION & TREND RADAR (WSL Background Daemon)                |
|  - Agent Reach (twitter-cli, rdt-cli, yt-dlp) scrapes X, Reddit & YouTube (₹0)    |
|  - Outlier Scorer (Python + DuckDB) ranks viral hooks vs. baseline engagement     |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
| LAYER 2: LOCAL CONTENT & MEDIA STUDIO (CPU-First, No Paid Media APIs)             |
|  - LLM writes JSON Storyboard + Platform-Specific Copy (X Thread, IG, YT Short)   |
|  - Voiceover: Kokoro-82M TTS (24kHz WAV on CPU) or VoiceStudio (Cloned Voice)     |
|  - Visuals: HyperFrames (HTML/CSS Motion Graphics to MP4) + Pillow Hook Cards     |
|  - Captions: Faster-Whisper (int8) -> Word-level .ass burned via FFmpeg           |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
| LAYER 3: OS-LEVEL ANTI-SHADOWBAN & METADATA SANITIZER                             |
|  - Python `watchdog` detects newly rendered MP4 in `/jobs/ready_to_clean/`        |
|  - FFmpeg adds imperceptible noise/pitch micro-shift + ExifTool injects iPhone    |
|    QuickTime metadata so platforms treat the file as an organic mobile upload     |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
| LAYER 4: HUMAN-IN-THE-LOOP APPROVAL & SCHEDULING (PocketBase + Ntfy)              |
|  - PocketBase logs the asset & sends a preview alert to your phone via Ntfy       |
|  - One-click Approve webhook moves the job to `/jobs/approved_queue/`             |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
| LAYER 5: OS-LEVEL STEALTH EXECUTION & MULTI-PLATFORM PUBLISHING                   |
|  - Primary Engine: `nodriver` or `Camoufox` with persistent isolated OS profiles  |
|  - Replay Engine: `browser-use` (with Telemetry=OFF) or `postiz-agent` CLI        |
|  - Human Behavior Layer: Bezier mouse curves, randomized typing cadence (40-110ms)|
|    and randomized cron jitter so posts never fire at exact `:00` second marks     |
+-----------------------------------------------------------------------------------+
```

---

## Part 4: Proposed Repository Structure for Your Project

```text
os-social-autopilot/
├── .env                         # ANONYMIZED_TELEMETRY=false, NTFY_TOPIC, etc.
├── pyproject.toml               # Managed via `uv` for 100x faster dependency locking
├── config/
│   ├── accounts.yaml            # Isolated browser profile paths & proxy bindings
│   └── schedule_rules.yaml      # Jitter windows, daily limits, warm-up rules
├── daemon/
│   ├── watcher.py               # Python `watchdog` OS file-system event listener
│   ├── scheduler.py             # Async cron loop with randomized human jitter
│   └── notifier.py              # Ntfy push notification & approval webhook handler
├── intelligence/
│   ├── agent_reach_bridge.py    # Wrapper for twitter-cli, rdt-cli, yt-dlp
│   └── outlier_ranker.py        # DuckDB query engine to score viral topics
├── studio/
│   ├── tts_kokoro.py            # Kokoro-82M local CPU voice synthesis
│   ├── whisper_ass.py           # Faster-Whisper word-level subtitle generator
│   ├── hyperframes_render.py    # HTML/CSS animation to MP4 renderer
│   └── sanitizer.py             # FFmpeg + ExifTool anti-shadowban metadata spoofer
├── executor/
│   ├── stealth_browser.py       # Camoufox / nodriver profile & cookie manager
│   ├── human_input.py           # Bezier mouse movement & realistic keystroke cadence
│   └── workflows/
│       ├── x_publisher.py       # Thread & video uploader for X
│       ├── yt_shorts.py         # YouTube Studio headless/GUI uploader
│       └── ig_reels.py          # Instagram Reels uploader with mobile viewport emulation
└── storage/
    ├── autopilot.db             # SQLite / PocketBase state store
    └── dropzone/                # OS folders: /incoming, /sanitized, /published
```

---

## Part 5: 4-Phase Implementation Roadmap (Step-by-Step)

### Phase 1: The OS Foundation & Trend Radar (Week 1)
1. Initialize the project using **`uv`** (`uv init os-social-autopilot`) inside WSL.
2. Set up **`Agent Reach`** (`twitter-cli`, `rdt-cli`, `yt-dlp`) with a secondary account's browser cookies and build `outlier_ranker.py` using **`DuckDB`** to store and score daily scraped posts.
3. Spin up **`PocketBase`** (single binary) to hold your `posts_queue` table and connect **`Ntfy`** so your script can ping your phone.

### Phase 2: The Zero-Cost Media & Sanitizer Pipeline (Week 2)
1. Integrate the **`Kokoro-82M`** + **`Faster-Whisper`** + **`FFmpeg`** pipeline we designed earlier.
2. Add **`HyperFrames`** so your script can generate animated data/code visuals from HTML templates without needing stock video APIs.
3. Build `sanitizer.py`: run an automatic post-processing command that strips `Lavf` FFmpeg headers and writes Apple iPhone metadata tags using `exiftool`.

### Phase 3: OS-Level Stealth Browser & Upload Executor (Week 3)
1. Set up **`nodriver`** (for Chrome-based persistent profiles) and **`Camoufox`** (for strict anti-fingerprint isolation).
2. Write `human_input.py` to inject randomized delays (`random.uniform(0.8, 2.4)`), natural scrolling, and human typing intervals.
3. Build deterministic upload scripts for X, YouTube Shorts, and Instagram Reels, using **`browser-use`** (`ANONYMIZED_TELEMETRY=false`) only as a fallback when a platform changes its button selectors.

### Phase 4: OS File-System Daemon & Guardrails (Week 4)
1. Wire up Python **`watchdog`** in `daemon/watcher.py` so dropping any `.json` brief or `.mp4` video into `storage/dropzone/incoming/` automatically runs sanitization, queues the post, and requests approval via `Ntfy`.
2. Add **`perplexityai/bumblebee`** to scan any third-party MCP skills or npm packages before running them on your host OS.

---

## Part 6: Critical OS-Level Anti-Ban & Security Rules

1. **Never Post on Exact Minute Marks:** Bots post at `12:00:00`. Always add a Gaussian jitter (e.g., `12:00` + `random(140, 890)` seconds) in your OS scheduler.
2. **One Persistent Browser Profile Per Account Pool:** Store browser user-data directories on disk (`/profiles/account_1`) so cookies, `localStorage`, and IndexedDB persist naturally across runs—never log in from scratch on every script execution.
3. **Disable Telemetry in Open-Source Agent Libraries:** Set `ANONYMIZED_TELEMETRY=false` in `browser-use` and similar tools so your session URLs and social media handles never leave your machine.
4. **Strip FFmpeg Signatures:** Always pass `-map_metadata -1` and inject clean device tags before uploading to TikTok, Instagram Reels, or YouTube Shorts.