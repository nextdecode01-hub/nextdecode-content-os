# NEXTDECODE Content Format Routing Contract

Status: first implementation increment; not a declaration that every channel format is production-ready.

## Request contract

The authenticated `POST /start` request accepts `content_format`. Existing clients remain compatible: an omitted value defaults to `youtube_shorts`. The value is validated against `app/content/formats.py`; unknown values are rejected with HTTP 400 and declared-but-unimplemented formats are rejected with HTTP 422.

`GET /content-formats` exposes each format's producer, status, platforms and capability note. Consumers must treat `not_implemented` as unavailable, not as a queued or partially supported feature.

## Current producer routing

| Format | Producer | Status | Notes |
|---|---|---|---|
| `youtube_shorts` | Existing vertical short pipeline | supported | Existing strong/legacy quality and storyboard gates remain in force |
| `instagram_reels` | Existing vertical short pipeline | supported | Generation only; destination-specific publish still uses existing approval/publishing path |
| `facebook_reels` | Existing vertical short pipeline | supported | Generation only; destination-specific publish still uses existing approval/publishing path |
| `youtube_longform` | Existing `pipelines.longform` | supported with constraints | Horizontal render path; API dry-run is refused because no safe long-form dry-run exists |
| `youtube_community_posts` | — | not_implemented | No complete post artifact/QA/review/publish chain |
| `instagram_posts` | — | not_implemented | No complete image-post artifact/QA/review/publish chain |
| `instagram_carousels` | — | not_implemented | No slide-pack artifact/QA/review/publish chain |
| `facebook_posts` | — | not_implemented | No complete post artifact/QA/review/publish chain |
| `linkedin_posts` | — | not_implemented | No complete post artifact/QA/review/publish chain |
| `x_posts` | — | not_implemented | No complete post/thread artifact/QA/review/publish chain |

## Safety and compatibility

- Existing API requests without `content_format` continue to select `youtube_shorts`.
- The API routes only to existing producer modules; it does not infer a publisher from a format name.
- A generated video job is not a publishing authorization. Human review/approval and the existing protected publishing boundary remain separate.
- Long-form requests with `dry_run=true` fail before invoking the producer. Set `dry_run=false` only to explicitly request a real draft render; this does not authorize public publishing.
- The format registry does not mark post/carousel publishing as available merely because social platforms have API integrations.
- The research/story package remains the editorial source of truth. Platform-native adaptation, citations, media assets, and review artifacts are still required before additional formats can be enabled.

## Next implementation requirements

1. Add a shared, immutable story-package contract with source/claim provenance.
2. Build post and carousel artifact producers (copy, citations, image/slide assets and platform constraints).
3. Add format-specific QA and approval bindings; do not reuse video approval for image/text artifacts.
4. Add destination adapters only after artifact integrity, rights, approval and idempotency checks exist.
5. Add format-aware metadata, analytics and channel-specific performance feedback.
6. Qualify each format end-to-end in dry-run and human-approved private/test destinations before changing its status to `supported`.
