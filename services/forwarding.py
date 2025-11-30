import asyncio
from typing import Optional
from aiogram import Bot
from aiogram.types import Message
import logging

async def get_bot_link(bot: Bot) -> str:
    """Get the bot's Telegram link with caching"""
    try:
        bot_info = await bot.get_me()
        return f"https://t.me/{bot_info.username}" if bot_info.username else ""
    except Exception as e:
        logging.exception("Failed to get bot link")
        return ""

async def forward_any(bot: Bot, message: Message, target_chat_id: int, prefix: Optional[str] = None, thread_id: Optional[int] = None) -> bool:
    """Generic function to forward any message content to a target chat"""
    try:
        user_info = ""
        if prefix:
            user_info = f"{prefix}\n\n"

        # Handle different message types
        if message.text:
            text_content = f"{user_info}{message.text}"
            await bot.send_message(target_chat_id, text_content, message_thread_id=thread_id)
        elif message.photo:
            caption = f"{user_info}{message.caption}" if message.caption else user_info
            await bot.send_photo(target_chat_id, message.photo[-1].file_id, caption=caption, message_thread_id=thread_id)
        elif message.video:
            caption = f"{user_info}{message.caption}" if message.caption else user_info
            await bot.send_video(target_chat_id, message.video.file_id, caption=caption, message_thread_id=thread_id)
        elif message.voice:
            caption = f"{user_info}{message.caption}" if message.caption else user_info
            await bot.send_voice(target_chat_id, message.voice.file_id, caption=caption, message_thread_id=thread_id)
        elif message.audio:
            caption = f"{user_info}{message.caption}" if message.caption else user_info
            await bot.send_audio(target_chat_id, message.audio.file_id, caption=caption, message_thread_id=thread_id)
        elif message.document:
            caption = f"{user_info}{message.caption}" if message.caption else user_info
            await bot.send_document(target_chat_id, message.document.file_id, caption=caption, message_thread_id=thread_id)
        elif message.animation:
            caption = f"{user_info}{message.caption}" if message.caption else user_info
            await bot.send_animation(target_chat_id, message.animation.file_id, caption=caption, message_thread_id=thread_id)
        elif message.sticker:
            await bot.send_message(target_chat_id, f"{user_info}[Sent a sticker]", message_thread_id=thread_id)
            await bot.send_sticker(target_chat_id, message.sticker.file_id, message_thread_id=thread_id)
        elif message.video_note:
            await bot.send_message(target_chat_id, f"{user_info}[Sent a video note]", message_thread_id=thread_id)
            await bot.send_video_note(target_chat_id, message.video_note.file_id, message_thread_id=thread_id)
        elif message.contact:
            await bot.send_contact(target_chat_id, phone_number=message.contact.phone_number,
                                   first_name=message.contact.first_name, last_name=message.contact.last_name,
                                   message_thread_id=thread_id)
            await bot.send_message(target_chat_id, f"{user_info}[Sent a contact]", message_thread_id=thread_id)
        elif message.location:
            await bot.send_location(target_chat_id, latitude=message.location.latitude,
                                    longitude=message.location.longitude, message_thread_id=thread_id)
            await bot.send_message(target_chat_id, f"{user_info}[Sent a location]", message_thread_id=thread_id)
        elif message.forward_from or message.forward_from_chat:
            try:
                await message.forward(target_chat_id, message_thread_id=thread_id)
                await bot.send_message(target_chat_id, f"{user_info}[Forwarded message]", message_thread_id=thread_id)
            except Exception as e:
                logging.warning(f"Could not forward message: {e}")
                await bot.send_message(target_chat_id, f"{user_info}[Could not forward message - content may be protected]", message_thread_id=thread_id)
        else:
            await bot.send_message(target_chat_id, f"{user_info}[Sent unsupported content type]", message_thread_id=thread_id)
        return True
    except Exception as e:
        logging.exception(f"Error forwarding message: {e}")
        return False
