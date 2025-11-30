from aiogram import Bot
from config import config
from db.repository import get_user_topic, save_user_topic, get_user_by_topic
import logging

async def get_or_create_user_topic(bot: Bot, tg_user_id: int, username: str = None, first_name: str = None) -> int:
    existing_topic_id = await get_user_topic(tg_user_id)
    if existing_topic_id:
        return existing_topic_id
    
    topic_name = f"{first_name or 'User'} (@{username})" if username else f"User {tg_user_id}"
    if len(topic_name) > 128:
        topic_name = topic_name[:125] + "..."
    
    try:
        result = await bot.create_forum_topic(chat_id=config.STAFF_CHAT_ID, name=topic_name)
        topic_id = result.message_thread_id
        
        existing_user = await get_user_by_topic(topic_id)
        if existing_user:
            return topic_id
        
        await save_user_topic(tg_user_id, topic_id, topic_name)
        logging.info(f"✅ Created forum topic {topic_id} for user {tg_user_id}")
        return topic_id
    except Exception as e:
        logging.warning(f"Could not create forum topic: {e}")
        return None
