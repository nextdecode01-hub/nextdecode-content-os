# Production scene tools

## Playwright browser capture
`capture_browser_scene.mjs` captures an authorized browser page at 1080×1920. It checks for Playwright at runtime; no package is installed automatically. Install Playwright + Chromium only after owner approval.

Use only pages the production team is authorized to access. Do not capture account pages, private user data, tokens, payment screens or personal information. Prefer a sanitized staging/demo page. Store URL, capture timestamp and project/run ID with each captured asset.

## Remotion
The `remotion/` directory is a starter composition layer. React/Remotion dependencies and Chromium render binaries are not installed. Remotion should render isolated scene clips to MP4, then the existing FFmpeg editor/EDL pipeline can consume them as source shots. Do not replace the main renderer.
