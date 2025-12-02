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
    
    # Ignore commands in the general staff chat handler
    if message.text and message.text.startswith('/'):
        return
    
    topic_id = getattr(message, 'message_thread_id', None)
    if not topic_id:
        # Not in a topic; ignore in this handler
        return
    
    user_id = await get_user_by_topic(topic_id)
    if not user_id:
        logging.warning(f"No user found for topic {topic_id}")
        return
    
    # Forward staff message to the specific user without any extra label
    success = await forward_any(message.bot, message, user_id)
    if success:
        logging.info(f"Forwarded staff message from topic {topic_id} to user {user_id}")
    else:
        logging.error(f"Failed to forward staff message from topic {topic_id} to user {user_id}")

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
    
    parts = msg.text.split(None, 1)
    content = parts[1] if len(parts) > 1 else ""
    if not content:
        await msg.reply("No reply text provided.")
        return
    
    try:
        # Send reply to user directly, no label
        await msg.bot.send_message(tg_id, content)
        await msg.reply("✅ Sent to user.")
    except Exception as e:
        logging.exception(f"Error sending reply to user {tg_id}: {e}")
        await msg.reply(f"❌ Error sending message to user: {e}")

@router.message(F.chat.id == config.STAFF_CHAT_ID, F.message_thread_id.is_not(None))
async def handle_staff_replies(message: types.Message):
    """Forward staff replies in topics back to users, without labels."""
    if message.from_user and message.from_user.is_bot:
        return
    
    topic_id = message.message_thread_id
    user_id = await get_user_by_topic(topic_id)
    if not user_id:
        logging.warning(f"No user found for topic {topic_id}")
        return
    
    try:
        success = await forward_any(message.bot, message, user_id)
        if success:
            logging.info(f"Forwarded staff reply from topic {topic_id} to user {user_id}")
        else:
            logging.error(f"Failed to forward staff reply from topic {topic_id} to user {user_id}")
    except Exception as e:
        logging.error(f"Failed to forward staff reply: {e}")
