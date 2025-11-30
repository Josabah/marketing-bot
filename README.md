# Marketing Campaign Bot

A Telegram bot for managing marketing campaigns with invite tracking, user rankings, and submission handling.

## Features

- **Invite Link Generation**: Creates unique invite links for each user
- **Join Tracking**: Tracks when users join via invite links
- **User Rankings**: Ranks users based on the number of invites
- **Submission System**: Users can submit proof (media/files) for review
- **Support System**: Users can contact staff for support
- **Staff Commands**: Staff can reply to users and export submissions

## Prerequisites

- Python 3.8 or higher
- A Telegram Bot Token (get from [@BotFather](https://t.me/BotFather))
- A Telegram Channel where the bot is an admin
- A Staff Chat/Group for receiving submissions and support messages

## Installation

1. **Clone or download this repository**

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Create a `.env` file**:
   ```bash
   cp .env.example .env
   ```
   Then edit `.env` and fill in your actual values (see Configuration section below).

## Configuration

### Getting Your Bot Token

1. Open Telegram and search for [@BotFather](https://t.me/BotFather)
2. Send `/newbot` and follow the instructions
3. Copy the bot token you receive

### Getting Channel and Chat IDs

You can use one of these bots to get IDs:
- [@userinfobot](https://t.me/userinfobot) - Add to your channel/group and it will show the ID
- [@getidsbot](https://t.me/getidsbot) - Another option for getting IDs

For channels:
- Make sure to forward a message from your channel to the bot, or add the bot to your channel as admin first

### Setting Up the Bot as Admin

**IMPORTANT**: The bot must be an admin in your Telegram channel to create invite links.

1. Go to your Telegram channel
2. Click on the channel name → "Administrators"
3. Click "Add Administrator"
4. Search for your bot and add it
5. Grant it permission to "Invite users via link" (at minimum)

### Environment Variables

Create a `.env` file in the project root with these variables:

| Variable | Description | Required |
|----------|-------------|----------|
| `BOT_TOKEN` | Your bot token from @BotFather | Yes |
| `CHANNEL_ID` | The ID of your Telegram channel | Yes |
| `STAFF_CHAT_ID` | Chat ID where submissions/support messages go | Yes |
| `JOIN_REQUESTS_ENABLED` | Enable join requests (yes/no) | No (default: yes) |
| `CAMPAIGN_HEADER` | Header message with {} placeholders | No |
| `SHARE_BODY` | Share message body with <INVITE_LINK> placeholder | No |

## Running the Bot

### Development

Simply run:
```bash
python bot.py
```

### Production

For production, you should use a process manager to keep the bot running:

**Option 1: Using screen**
```bash
screen -S marketing_bot
python bot.py
# Press Ctrl+A then D to detach
```

**Option 2: Using systemd (Linux)**
Create `/etc/systemd/system/marketing-bot.service`:
```ini
[Unit]
Description=Marketing Campaign Bot
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/Marketing Campaign Bot
ExecStart=/usr/bin/python3 bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable marketing-bot
sudo systemctl start marketing-bot
```

**Option 3: Using supervisor**
Create a supervisor config file and run:
```bash
supervisord -c supervisor.conf
```

## Bot Commands

### User Commands

- `/start` - Start the bot and get your invite link
- `My Stats` button - View your invite count and ranking
- `Contact Support` button - Send a support message to staff
- Send media/files - Submit proof for review

### Staff Commands (only work in staff chat)

- `/reply <message>` - Reply to a user's submission or support message (reply to their message first)
- `/export_submissions` - Export the last 50 submissions

## How It Works

1. User sends `/start` to the bot
2. Bot creates a unique invite link for the user
3. Bot shows campaign message with share button
4. User shares the message via the button
5. When someone joins via the invite link, it's tracked
6. User can submit proof by sending media/files to the bot
7. Staff receives submissions in the staff chat and can reply

## Database

The bot uses SQLite database (`havan_bot.db`) which is automatically created on first run. It stores:
- User information
- Invite links
- Join events
- Submissions

## Troubleshooting

### Bot can't create invite links
- Make sure the bot is an admin in your channel
- Make sure the bot has permission to "Invite users via link"
- Check that `CHANNEL_ID` is correct

### Bot not responding
- Check that `BOT_TOKEN` is correct
- Verify all environment variables are set
- Check bot logs for errors

### Join requests not working
- Make sure `JOIN_REQUESTS_ENABLED=yes` in `.env`
- Verify the bot has permission to approve join requests

## License

This project is provided as-is for your use.

## Support

For issues with this bot, check the logs or contact your development team.
