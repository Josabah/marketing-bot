from aiogram import Bot
from config import config
from db.repository import get_user_topic, save_user_topic
import logging
from aiogram.exceptions import TelegramBadRequest

async def get_or_create_user_topic(bot: Bot, tg_user_id: int, username: str = None, first_name: str = None) -> int:
    existing_topic_id = await get_user_topic(tg_user_id)
    if existing_topic_id:
        try:
            # Probe existing topic; if works, reuse
            probe = await bot.send_message(config.STAFF_CHAT_ID, "\u2063", message_thread_id=existing_topic_id)
            try:
                await bot.delete_message(config.STAFF_CHAT_ID, probe.message_id)
            except Exception:
                pass
            return existing_topic_id
        except TelegramBadRequest:
            logging.warning(f"Topic {existing_topic_id} deleted for user {tg_user_id}, will recreate.")
        except Exception as e:
            logging.warning(f"Error probing topic {existing_topic_id}: {e}. Will recreate.")
    # Create new topic (only after probe fails)
    topic_name = f"{first_name or 'User'} (@{username})" if username else f"User {tg_user_id}"
    if len(topic_name) > 128:
        topic_name = topic_name[:125] + "..."
    try:
        result = await bot.create_forum_topic(chat_id=config.STAFF_CHAT_ID, name=topic_name)
        topic_id = result.message_thread_id
        await save_user_topic(tg_user_id, topic_id, topic_name)
        logging.info(f"Created new topic {topic_id} for user {tg_user_id}")
        return topic_id
    except Exception as e:
        logging.warning(f"Failed to create forum topic for user {tg_user_id}: {e}")
        return None
