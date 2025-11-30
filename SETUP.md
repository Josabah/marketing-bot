# Quick Setup Guide

Follow these steps to get your bot up and running:

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Create .env File

Create a file named `.env` in this directory with the following content:

```env
BOT_TOKEN=your_bot_token_here
CHANNEL_ID=your_channel_id_here
STAFF_CHAT_ID=your_staff_chat_id_here
JOIN_REQUESTS_ENABLED=yes
CAMPAIGN_HEADER=Share Havan Academy to your classmates\nTotal Invited: {}\nRank:{}
SHARE_BODY=
```

### Getting Your Values:

**BOT_TOKEN:**
1. Open Telegram and search for [@BotFather](https://t.me/BotFather)
2. Send `/newbot` and follow instructions
3. Copy the token you receive

**CHANNEL_ID:**
- Add [@userinfobot](https://t.me/userinfobot) to your channel
- Or forward a message from your channel to [@getidsbot](https://t.me/getidsbot)
- The ID will be a negative number (e.g., -1001234567890)

**STAFF_CHAT_ID:**
- Can be your personal chat ID (positive number)
- Or a group chat ID (negative number)
- Use the same bots as above to get the ID

**SHARE_BODY:** (Optional)
- Leave empty to use default Amharic text
- Or provide your custom message with `<INVITE_LINK>` placeholder

## Step 3: Make Bot Admin

**CRITICAL:** Your bot MUST be an admin in your channel to create invite links!

1. Go to your Telegram channel
2. Click channel name → "Administrators" or "Manage Channel"
3. Click "Add Administrator"
4. Search for your bot username
5. Give it permission to "Invite users via link"
6. Save

## Step 4: Run the Bot

```bash
python bot.py
```

If everything is configured correctly, you should see:
```
INFO:__main__:DB initialized
INFO:__main__:Bot @your_bot_username started
```

## Troubleshooting

**"BOT_TOKEN environment variable is required"**
→ Create the `.env` file with your bot token

**"Failed creating invite link"**
→ Make sure bot is admin in channel with invite permissions

**"Chat not found"**
→ Check that CHANNEL_ID and STAFF_CHAT_ID are correct

**Bot doesn't respond**
→ Check the console for error messages
→ Verify BOT_TOKEN is correct
→ Make sure bot is running (check with /start command)

## Next Steps

Once running:
1. Test with `/start` command
2. Check that invite links are created
3. Test joining via invite link
4. Verify submissions are forwarded to staff chat

## Production Deployment

For production, use a process manager:

**Using screen:**
```bash
screen -S bot
python bot.py
# Press Ctrl+A, then D to detach
```

**Using tmux:**
```bash
tmux new -s bot
python bot.py
# Press Ctrl+B, then D to detach
```

To reattach: `screen -r bot` or `tmux attach -t bot`
