# bot.py
import os
import logging
import asyncio
import re
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from urllib.parse import quote_plus
import db
from datetime import datetime

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
STAFF_CHAT_ID = os.getenv("STAFF_CHAT_ID")

# Validate required environment variables
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required. Please set it in your .env file.")
if not CHANNEL_ID:
    raise ValueError("CHANNEL_ID environment variable is required. Please set it in your .env file.")
if not STAFF_CHAT_ID:
    raise ValueError("STAFF_CHAT_ID environment variable is required. Please set it in your .env file.")

try:
    CHANNEL_ID = int(CHANNEL_ID)
    STAFF_CHAT_ID = int(STAFF_CHAT_ID)
except ValueError as e:
    raise ValueError(f"CHANNEL_ID and STAFF_CHAT_ID must be valid integers. Error: {e}")
JOIN_REQUESTS_ENABLED = os.getenv("JOIN_REQUESTS_ENABLED", "yes").lower() == "yes"
CAMPAIGN_HEADER = os.getenv("CAMPAIGN_HEADER", "Share Havan Academy to your classmates\nTotal Invited: {}\nRank:{}")

# Full Amharic text for sharing
SHARE_BODY = os.getenv("SHARE_BODY")
if not SHARE_BODY:
    SHARE_BODY = (
        "ወሳኝ ነገር Online ለሆናችሁ ፍሬሽማን ተማሪዎች🎉\n\n"
        "ዩኒቨርስቲ ላይ GPA four ማምጣት በጣም ቀላል ነው። ፍሬሽማንን በስኬት አጠናቀው የፈለጉት ዲፓርትመንት የሚገቡ ልጆች ሌት እና ቀን የሚያጠኑት ብቻ አይደሉም።  "
        "ዩኒቨርስቲ ላይ ፈተና ይደጋገማል።ይሄ ማንም የሚያውቀው ነገር ነው ነገር ግን የተደራጁ ፈተናዎችን ማግኘት አስቸጋሪ ከመሆኑ የተነሳ "
        "ሳናስበው ጥያቄዎችን ሳንሰራ እንገባለን። ትልቅ ስህተት!😨\n\n"
        "የዚህ አመት ፍሬሽማኖች በጣም እድለኞች ናችሁ። ሃቫን  በቴሌግራም ላይ የተበተኑትን የmid እና የfinal exam ፈተናዎች "
        "በዩኒቨርስቲ፣ በsubject እና በአመተ ምህረት አደራጅተን እየለቀቅን ነው። 💪\n\n"
        "ከ34.8 ሺ በላይ የፍሬሽማን ተማሪዎች በሚከተሉት የቴሌግራም ቻናላችን ላይ ሁሉንም በነጻ ታገኛላችሁ።👇👇👇\n\n"
        "👉<INVITE_LINK>👆👆\n\n"
        "ከዛሬ ውጭ ሊንኩ አይሰራላችሁም። አሁኑኑ Join በሉ።"
    )

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Initialize DB on startup
async def on_startup():
    await db.init_db()
    logging.info("DB initialized")

async def make_or_get_invite(tg_user_id, user_fullname):
    # Check DB first
    link = await db.get_invite_by_user(tg_user_id)
    if link:
        return link

    # Create invite link via API
    # create_chat_invite_link requires the bot to be admin in the channel
    name = f"user_{tg_user_id}"
    try:
        params = {
            "chat_id": CHANNEL_ID,
            "name": name,
        }
        # If join requests desired, set creates_join_request
        if JOIN_REQUESTS_ENABLED:
            params["creates_join_request"] = True
        res = await bot.create_chat_invite_link(**params)
        invite_link = res.invite_link
        await db.save_invite_link(invite_link, tg_user_id)
        return invite_link
    except Exception as e:
        logging.exception("Failed creating invite link: %s", e)
        return None

async def build_share_url(invite_link, share_text):
    # Embed invite_link into the share_text (replace placeholder <INVITE_LINK> if present)
    body = share_text.replace("<INVITE_LINK>", invite_link)
    # Telegram share deeplink uses url and text
    # url param can be the bot or channel link; we just include invite link in text and keep url empty or set to bot
    try:
        bot_info = await bot.get_me()
        url_param = f"https://t.me/{bot_info.username}" if bot_info.username else ""
    except:
        url_param = ""
    u = f"https://t.me/share/url?text={quote_plus(body)}"
    if url_param:
        u += f"&url={quote_plus(url_param)}"
    return u

def campaign_keyboard(share_url):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Share to Group", url=share_url)],
            [
                InlineKeyboardButton(text="Submit Proof (forward media here)", callback_data="noop"),
                InlineKeyboardButton(text="Contact Support", callback_data="contact_support")
            ],
            [InlineKeyboardButton(text="My Stats", callback_data="my_stats")]
        ]
    )
    return kb

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    tg_id = message.from_user.id
    await db.ensure_user(tg_id, message.from_user.username, message.from_user.first_name)
    # create invite link
    invite_link = await make_or_get_invite(tg_id, f"{message.from_user.first_name or ''}")
    if not invite_link:
        await message.reply("Error creating invite link. Please contact support.")
        return

    # compute stats - only counts joins via bot-created invite links
    total_invites = await db.get_user_join_count(tg_id)
    rank, total = await db.get_rank(tg_id)
    # Prepare header
    header = CAMPAIGN_HEADER.format(total_invites, rank or "-")
    # Build the composed share text by inserting invite link into SHARE_BODY
    composed = SHARE_BODY.replace("<INVITE_LINK>", invite_link)
    share_url = await build_share_url(invite_link, composed)
    kb = campaign_keyboard(share_url)
    # Show full message text above buttons (no truncation)
    await message.reply(header + "\n\n" + composed, reply_markup=kb)

@dp.callback_query(lambda c: c.data == "my_stats")
async def cb_my_stats(query: types.CallbackQuery):
    tg_id = query.from_user.id
    await db.ensure_user(tg_id, query.from_user.username, query.from_user.first_name)
    count = await db.get_user_join_count(tg_id)
    rank, total = await db.get_rank(tg_id)
    rank_text = f"{rank}/{total}" if rank else f"Unranked (0/{total})"
    text = f"Your stats:\nTotal invited (via your link): {count}\nRank: {rank_text}"
    # Keep buttons visible - send new message instead of editing
    await query.message.answer(text)
    await query.answer()

@dp.callback_query(lambda c: c.data == "contact_support")
async def cb_contact(query: types.CallbackQuery):
    await query.message.answer("Send your message (text or voice) and staff will reply. Just send it as a normal message here.")
    await query.answer()
    
@dp.callback_query(lambda c: c.data == "noop")
async def cb_noop(query: types.CallbackQuery):
    """No-op handler for buttons that don't need action"""
    await query.answer("You can forward media files directly to this chat to submit proof.", show_alert=True)

@dp.message()
async def handle_all_messages(message: types.Message):
    """
    - Accept forwarded media (photo, video, animation, document). If message contains media and is in a private chat (user->bot),
      save submission and forward to staff group with metadata.
    - If user sends plain text in private chat starting with /, ignore (handled elsewhere). Otherwise, treat plain text as support message.
    """
    # only react to private chat user messages
    if message.chat.type != "private":
        return

    tg_id = message.from_user.id
    await db.ensure_user(tg_id, message.from_user.username, message.from_user.first_name)

    # if message has media (photo/video/animation/document) or is forwarded message with media, treat as submission
    file_ids = []
    if message.photo:
        # take highest resolution
        file_ids.append(message.photo[-1].file_id)
    if message.video:
        file_ids.append(message.video.file_id)
    if message.animation:
        file_ids.append(message.animation.file_id)
    if message.document:
        file_ids.append(message.document.file_id)
    # forwarded message can be anything; if forwarded, include as evidence by forwarding the message itself below
    is_forward = bool(message.forward_from or message.forward_from_chat)

    if file_ids or is_forward:
        # save submission
        saved_id = await db.save_submission(tg_id, [f for f in file_ids] or ["forwarded_message"], message.caption or "")
        # forward the entire message to staff group, but also send a metadata header
        meta = f"Submission #{saved_id} from @{message.from_user.username or 'unknown'} (id:{tg_id}) at {datetime.utcnow().isoformat()}"
        # first send meta then forward original
        await bot.send_message(STAFF_CHAT_ID, meta)
        try:
            if is_forward:
                # forward the message itself
                await message.forward(STAFF_CHAT_ID)
            else:
                # send each file as copy (use send_photo/send_video accordingly)
                for fid in file_ids:
                    # We'll send as document so it works for photo, video, doc
                    await bot.send_document(STAFF_CHAT_ID, fid, caption=f"Submission #{saved_id} from {tg_id}")
        except Exception as e:
            logging.exception("Error forwarding submission: %s", e)
            await bot.send_message(STAFF_CHAT_ID, "Error forwarding media; staff please check manually.")
        # ack to user (optional minimal)
        await message.reply("Proof received. Staff will review it manually. Thank you.")
        return

    # otherwise plain text -> treat as support message
    # forward the message content to staff with metadata and allow staff to reply via /reply
    meta = f"Support message from @{message.from_user.username or 'unknown'} (id:{tg_id})"
    await bot.send_message(STAFF_CHAT_ID, meta + "\n\n" + (message.text or "<no text>"))
    await message.reply("Support message received. Staff will reply via the bot soon.")

@dp.chat_join_request()
async def handle_join_request(update: types.ChatJoinRequest):
    """
    When join requests arrive, only record joins via invite links created by this bot.
    Only links stored in our database (bot-created) will be counted in stats.
    """
    try:
        invite_link = None
        # Try multiple ways to get the invite link (aiogram 3.x compatibility)
        if hasattr(update, 'invite_link') and update.invite_link:
            if hasattr(update.invite_link, 'invite_link'):
                invite_link = update.invite_link.invite_link
            elif isinstance(update.invite_link, str):
                invite_link = update.invite_link
        
        joining_user = update.from_user.id
        
        # Only record joins via invite links created by this bot (stored in our database)
        if invite_link:
            # Verify this invite link exists in our database before recording
            existing_link = await db.get_invite_by_link(invite_link)
            if existing_link:
                await db.record_join(invite_link, joining_user)
                logging.info(f"Recorded join for user {joining_user} via bot-created link")
            else:
                logging.info(f"Ignoring join from user {joining_user} via non-bot invite link")
        
        # Approve the join request automatically
        await bot.approve_chat_join_request(chat_id=CHANNEL_ID, user_id=joining_user)
        
        # Notify staff only for bot-created links
        if invite_link:
            existing_link = await db.get_invite_by_link(invite_link)
            if existing_link:
                await bot.send_message(STAFF_CHAT_ID, f"User {update.from_user.id} joined via bot invite link {invite_link}. Auto-approved and logged.")
    except Exception as e:
        logging.exception("Error handling join request: %s", e)
        await bot.send_message(STAFF_CHAT_ID, f"Error handling join request: {e}")

# Staff helper: /reply -> staff replies to the previous forwarded submission message
@dp.message(Command("reply"))
async def staff_reply(msg: types.Message):
    # Only allow in staff chat
    if msg.chat.id != STAFF_CHAT_ID:
        return
    # staff should reply to the metadata message or forwarded message
    if not msg.reply_to_message:
        await msg.reply("Use this command as a reply to the submission message in staff chat. Example: reply <text>")
        return
    # Retrieve the original metadata message text to find tg_user_id
    text = msg.reply_to_message.text or ""
    # Try to parse id: look for pattern id:<tg_id>
    m = re.search(r"id:(\d+)", text)
    if not m:
        await msg.reply("Could not find user id in the replied message header. Make sure you reply to a submission header.")
        return
    tg_id = int(m.group(1))
    # Build reply content: take staff message text minus the /reply command
    if not msg.text:
        await msg.reply("No reply text provided. Usage: /reply <your message>")
        return
    parts = msg.text.split(None, 1)
    content = parts[1] if len(parts) > 1 else ""
    if not content:
        await msg.reply("No reply text provided. Usage: /reply <your message>")
        return
    await bot.send_message(tg_id, f"Staff reply: {content}")
    await msg.reply("Sent to user.")

# Staff command to export submissions
@dp.message(Command("export_submissions"))
async def export_submissions(msg: types.Message):
    if msg.chat.id != STAFF_CHAT_ID:
        return
    import aiosqlite
    out = []
    async with aiosqlite.connect(db.DB_PATH) as conn:
        cur = await conn.execute(
            "SELECT id, tg_user_id, file_ids, caption, created_at, staff_handled FROM submissions ORDER BY created_at DESC LIMIT 50"
        )
        rows = await cur.fetchall()
        for r in rows:
            out.append(f"{r[0]} | user:{r[1]} | files:{r[2]} | caption:{r[3]} | at:{r[4]} | handled:{r[5]}")
    await msg.reply("\n".join(out) if out else "no submissions")

if __name__ == "__main__":
    async def main():
        await on_startup()
        # Fetch bot info to get username
        bot_info = await bot.get_me()
        logging.info(f"Bot @{bot_info.username} started")
        await dp.start_polling(bot, allowed_updates=["message", "callback_query", "chat_join_request"])
    
    asyncio.run(main())
