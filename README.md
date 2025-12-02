# Marketing Campaign Bot

A Telegram bot for Havan Academy’s invite campaign: generates personal invite links, tracks joins, forwards user messages to staff topics, and provides a persistent action menu.

## Features

- Personal invite links via Telegram API
- Join‑tracking and user rankings
- Auto‑created staff topics per user; recreates if deleted
- Persistent menu (ReplyKeyboard) and inline Share button
- Clean UX (no noisy confirmations; warns only on failure)

## Requirements

- Python 3.10+
- A Telegram bot token (BotFather)
- Bot must be admin in:
  - Your campaign channel (to create invite links)
  - Staff supergroup with Topics enabled (to create/forward in threads)

## Setup

1. Create `.env` in project root:
   - `BOT_TOKEN=your_token`
   - `CHANNEL_ID=<channel_id>`
   - `STAFF_CHAT_ID=<staff_supergroup_id>`
   - `JOIN_REQUESTS_ENABLED=yes`
   - `DEBUG=false`
   - Optional: `CAMPAIGN_HEADER`, `SHARE_BODY`
2. Install dependencies:
   - `python3 -m venv .venv`
   - `source .venv/bin/activate`
   - `pip install -r requirements.txt`

## Run

- macOS/Linux:
  - `./start_bot.sh`
- Ensure no conflicts:
  - Disable webhook: `https://api.telegram.org/bot<token>/deleteWebhook`
  - Kill old processes if needed (macOS):
    - `pkill -f "python3 .*Marketing Campaign Bot/main.py"`
    - `pkill -f "python3 .*Marketing Campaign Bot/bot.py"`

## Usage

- `/start`: sends header + Amharic share text with your invite link, inline Share button, and loads persistent menu.
- Persistent “Share to Group”: prompts with the same inline Share button to open Telegram’s share sheet.
- Messages in DM: forwarded only to your staff topic; if the topic was deleted, the bot recreates one and uses it.
- Staff replies inside a topic: forwarded back to the user without extra labels.

## Notes

- Amharic content is sent as plain text to avoid Markdown parse errors.
- Link previews are disabled in bot messages to keep them concise.
- Database: local SQLite (`havan_bot.db`) via `db/repository.py`.

## Scaling (recommendations)

- For 24/7 and high concurrency:
  - Switch to webhooks on a VPS (Nginx + TLS), run under systemd
  - Migrate DB to Postgres for concurrent writes
  - Add retry/backoff for rate limits (429), structured logging, and monitoring

## Troubleshooting

- “Conflict: terminated by other getUpdates”: stop other bot instances or delete webhook.
- “can’t parse entities”: avoid Markdown in Amharic or escape via MarkdownV2.
- Invite link failures: ensure bot is admin in the `CHANNEL_ID`.
- Topic creation failures: ensure `STAFF_CHAT_ID` is a supergroup with Topics enabled, and the bot is admin.
