# Notifications package

This package owns outbound user notifications. It is separate from approvals, publishing authorization and platform adapters.

## Modules

- `notify_status.py` — best-effort Telegram `sendMessage` transport.
- `notify_review.py` — prepares a private review reminder and delegates delivery to `notify_status`.

## Invocation

- `python -m app.notifications.notify_status "message"`
- `python -m app.notifications.notify_review short`
- `python -m app.notifications.notify_review longform`

No root-level forwarding or compatibility files are maintained.

## Security boundary

- Telegram is outbound-only.
- No webhook, polling, callback query, callback-data or approval command receiver exists.
- A Telegram message or tap is not a human approval decision and cannot grant publishing authorization.
- Review reminders contain a local preview path and a separate manual local approval command.
- Delivery failure does not alter pipeline, approval or publishing state.
- Never log or print a Telegram Bot API URL because the bot token is embedded in its path.
