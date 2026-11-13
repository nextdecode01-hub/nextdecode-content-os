# Remaining setup

The content generator has Gemini and Groq credentials in /home/demon/shorts_studio/.env. The publisher can still be prepared while the account-specific social credentials are completed.

## Already configured

- Gemini API key is set.
- Groq API key is set as an alternate provider.
- YouTube OAuth client ID and secret are set, and youtube_token.json is present. OAuth previously succeeded.

## Required for Facebook and Instagram Reels

1. Finish Meta developer account verification in Meta. Enter the phone number and SMS code directly in the Meta page.
2. Create/configure the Meta app for publishing and add the required Facebook and Instagram permissions. For the existing Facebook Login flow, the project documents the needed permissions in META_REELS_SETUP.md.
3. Link an Instagram Business or Creator account to the Facebook Page.
4. Obtain the Facebook Page ID, Page access token, Instagram professional account ID, and a compatible access token. Save them only in the WSL .env file.
5. Configure INSTAGRAM_VIDEO_URL to a stable public HTTPS URL for each generated MP4. Meta must be able to fetch the video directly. A stable host (object storage or a named Cloudflare tunnel with its own hostname) is the recommended path for scheduled runs.
6. Alternative for scheduled runs: set `INSTAGRAM_TUNNEL_FALLBACK=true` in `.env`. `publish_all.py` then starts a temporary Cloudflare Quick Tunnel for the duration of the run and passes the generated URL to the Instagram publisher. `cloudflared` must be installed and on PATH (`~/.local/bin/cloudflared`). The tunnel URL changes every run and the tunnel only lives while the publish run is active, so it is a fallback, not a replacement for a stable host.

The publisher scripts perform destination preflight and share the application-owned authorization boundary. Facebook/Instagram stay blocked until the Meta credentials and a public media host (stable URL or tunnel fallback) are ready. The autonomous task worker cannot upload or publish.

## Optional services

- Pexels B-roll: the project works without it. Pexels currently reports that new API key issuance is paused. Keep motion-background footage as the fallback until issuance resumes: https://help.pexels.com/hc/en-us/articles/900004904026-How-do-I-get-an-API-key
- Telegram alerts: create a bot through the official @BotFather with /newbot, then add TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID to .env. Do not share the token in chat. Official setup: https://core.telegram.org/bots/tutorial

After the remaining Meta setup, run setup_check.py from WSL. It reports readiness without showing credential values or publishing, and lists optional integrations separately from required setup blockers. It does not validate token permissions.

Keep all keys in /home/demon/shorts_studio/.env. Never commit the file or paste secrets into chat.
