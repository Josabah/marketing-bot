from aiogram import Router, types, F
from config import config
from db.repository import ensure_user
from services.topics import get_or_create_user_topic
from services.forwarding import forward_any

router = Router()

@router.message(F.chat.type == "private")
async def handle_user_messages(message: types.Message):
    if message.text and message.text.startswith('/'):
        return

    tg_id = message.from_user.id
    await ensure_user(tg_id, message.from_user.username, message.from_user.first_name)

    # Get or create forum topic for this user
    topic_id = await get_or_create_user_topic(message.bot, tg_id, message.from_user.username, message.from_user.first_name)

    # Forward all content types to staff chat
    user_info = f"From: @{message.from_user.username or 'unknown'} (ID: {message.from_user.id})"
    if message.from_user.first_name:
        user_info += f" - {message.from_user.first_name}"
    
    success = await forward_any(message.bot, message, config.STAFF_CHAT_ID, user_info, topic_id)
    
    if success:
        if message.photo or message.video or message.document or message.animation:
            await message.reply("✅ Your media has been forwarded to staff. They will review it soon.")
        elif message.voice or message.audio:
            await message.reply("✅ Your voice/audio message has been forwarded to staff. They will review it soon.")
        elif message.text:
            await message.reply("✅ Your message has been forwarded to staff. They will reply soon.")
        else:
            await message.reply("✅ Your message has been received and forwarded to staff.")
    else:
        await message.reply("⚠️ There was an error forwarding your message. Please try again or contact support.")
