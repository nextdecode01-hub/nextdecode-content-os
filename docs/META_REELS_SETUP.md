# Meta Reels publishing setup

This project now has separate publisher scripts for Facebook Page Reels and Instagram Reels. They use Meta's official upload and publish endpoints, check a per-platform upload ledger to avoid reposting identical content, and keep tokens out of source code.

## Accounts and permissions

- Facebook publishing needs a Facebook Page and a Page access token with publishing access.
- Instagram publishing through Facebook Login requires an Instagram Business or Creator account linked to a Facebook Page. The app needs `pages_show_list`, `pages_read_engagement`, `instagram_basic`, and `instagram_content_publish` permissions.
- For app-mode testing, the account must be an app role/tester. Public use may require Meta app review and advanced access.

## Add credentials to `.env`

```dotenv
META_GRAPH_API_VERSION=<Graph API version enabled for your Meta app>
FACEBOOK_PAGE_ID=<Facebook Page ID>
FACEBOOK_PAGE_ACCESS_TOKEN=<Page access token>
INSTAGRAM_USER_ID=<Instagram professional account ID>
INSTAGRAM_ACCESS_TOKEN=<Page/user access token authorized for Instagram publishing>
```

Keep these secrets in the WSL `.env`; never paste them into chat or commit them. `INSTAGRAM_ACCESS_TOKEN` can use the Page token from the Facebook Login flow if that token has the Instagram publishing permission.

## Getting the media to Instagram

Meta fetches the Instagram Reel video from a publicly reachable `video_url` and waits for the media container to reach `FINISHED` before publishing. The generator currently saves the MP4 only inside WSL.

For a stable daily workflow, configure a secure public video host and pass its per-run URL as `INSTAGRAM_VIDEO_URL`. `instagram_reels_upload.py` can use a temporary Cloudflare Quick Tunnel for a manual development check, but the scheduled `publish_all.py` preflight requires `INSTAGRAM_VIDEO_URL` so daily posting uses a stable host. Quick Tunnels have no uptime guarantee and are not used by the scheduled workflow.

## Temporary tunnel for scheduled runs

Set `INSTAGRAM_TUNNEL_FALLBACK=true` in `.env` to let `publish_all.py` open a Cloudflare Quick Tunnel itself for the duration of the publish run and hand the resulting URL to the Instagram publisher. This keeps the "no partial cross-post" rule intact, and the tunnel stays alive while Meta fetches the file. Install the binary with:

```
curl -fsSL -o ~/.local/bin/cloudflared https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
chmod +x ~/.local/bin/cloudflared
```

The hostname is different on every run and the tunnel disappears when the run ends, so a stable host remains the recommended setup. Remove the flag to require `INSTAGRAM_VIDEO_URL` again.

## n8n

The live n8n workflow calls `publish_all.py` after generation. It preflights YouTube, Facebook, and Instagram settings and stops before any upload if one destination is incomplete, so scheduled runs cannot quietly publish only to YouTube. Configure and verify all three publishers and a stable Instagram media host before activating the schedule.


