from aiogram import Router, types, F
from aiogram.filters import Command
import re
import logging
from config import config
from db.repository import get_user_by_topic
from services.forwarding import forward_any

router = Router()

@router.message(F.chat.id == config.STAFF_CHAT_ID)
async def handle_staff_chat_messages(message: types.Message):
    if message.from_user and message.from_user.is_bot:
        return
    
    if message.text and message.text.startswith('/reply'):
        return
    
    topic_id = getattr(message, 'message_thread_id', None)
    if not topic_id:
        return
    
    logging.info(f"Staff message in topic {topic_id}")
    user_id = await get_user_by_topic(topic_id)
    if user_id:
        logging.info(f"Forwarding staff message to user {user_id}")
        success = await forward_any(message.bot, message, user_id, "💬 Staff")
        if success:
            logging.info(f"Successfully forwarded to user {user_id}")
        else:
            logging.error(f"Failed to forward to user {user_id}")
    else:
        logging.warning(f"No user found for topic {topic_id}")

@router.message(Command("reply"))
async def staff_reply(msg: types.Message):
    if msg.chat.id != config.STAFF_CHAT_ID:
        return
    if not msg.reply_to_message:
        await msg.reply("Use this command as a reply to a user's message in staff chat. Example: /reply <your message>")
        return
    
    text = msg.reply_to_message.text or msg.reply_to_message.caption or ""
    tg_id = None
    m = re.search(r"ID:\s*(\d+)", text, re.IGNORECASE)
    if m:
        tg_id = int(m.group(1))
    
    if not tg_id:
        await msg.reply("Could not find user ID in the replied message.")
        return
    
    if not msg.text:
        await msg.reply("No reply text provided.")
        return
    parts = msg.text.split(None, 1)
    content = parts[1] if len(parts) > 1 else ""
    if not content:
        await msg.reply("No reply text provided.")
        return
    
    try:
        await msg.bot.send_message(tg_id, f"Staff reply: {content}")
        await msg.reply("✅ Sent to user.")
    except Exception as e:
        logging.exception(f"Error sending reply to user {tg_id}: {e}")
        await msg.reply(f"❌ Error sending message to user: {e}")

@router.message(Command("export_submissions"))
async def export_submissions(msg: types.Message):
    if msg.chat.id != config.STAFF_CHAT_ID:
        return
    import aiosqlite
    from db.repository import DB_PATH
    out = []
    async with aiosqlite.connect(DB_PATH) as conn:
        cur = await conn.execute(
            "SELECT id, tg_user_id, file_ids, caption, created_at, staff_handled FROM submissions ORDER BY created_at DESC LIMIT 50"
        )
        rows = await cur.fetchall()
        for r in rows:
            out.append(f"{r[0]} | user:{r[1]} | files:{r[2]} | caption:{r[3]} | at:{r[4]} | handled:{r[5]}")
    await msg.reply("\n".join(out) if out else "no submissions")

@router.message(F.chat.id == config.STAFF_CHAT_ID, F.message_thread_id.is_not(None))
async def handle_staff_replies(message: types.Message):
    """Forward staff replies in topics back to users."""
    if message.from_user and message.from_user.is_bot:
        return
    
    topic_id = message.message_thread_id
    user_id = await get_user_by_topic(topic_id)
    if user_id:
        try:
            # Forward the staff message to the user
            await forward_any(message.bot, message, user_id, "Staff reply")
            logging.info(f"Forwarded staff reply from topic {topic_id} to user {user_id}")
        except Exception as e:
            logging.error(f"Failed to forward staff reply: {e}")
    else:
        logging.warning(f"No user found for topic {topic_id}")
