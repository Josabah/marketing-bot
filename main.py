import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command
from aiogram import F
from urllib.parse import quote_plus
from config import config
from utils.logging import setup_logging
from db.repository import init_db
from services.invites import make_or_get_invite, build_share_url
from services.topics import get_or_create_user_topic
from services.forwarding import forward_any, get_bot_link
from keyboards.campaign import campaign_keyboard
from handlers import start, callbacks, user_messages, staff, join_requests, router as handlers_router

# Setup logging
setup_logging(config.DEBUG)

dp = Dispatcher()

# Include routers
dp.include_router(handlers_router)

async def on_startup(bot: Bot):
    await init_db()
    logging.info("DB initialized")

    # Environment checks
    try:
        me = await bot.get_me()
        logging.info(f"Bot @{me.username} (id={me.id}) connecting...")

        # Check channel access and admin rights
        try:
            ch = await bot.get_chat(config.CHANNEL_ID)
            logging.info(f"Channel chat type: {getattr(ch, 'type', None)}")
            member = await bot.get_chat_member(config.CHANNEL_ID, me.id)
            if getattr(member, 'status', '') not in ("administrator", "creator"):
                logging.warning("Bot is not admin in CHANNEL_ID. Invite link creation will fail.")
        except Exception as e:
            logging.error(f"Cannot access CHANNEL_ID {config.CHANNEL_ID}: {e}")

        # Check staff chat and forum capability
        try:
            staff_chat = await bot.get_chat(config.STAFF_CHAT_ID)
            is_forum = bool(getattr(staff_chat, 'is_forum', False))
            if not is_forum:
                logging.warning("STAFF_CHAT_ID is not a forum. Threaded topics will be disabled; use /reply command to answer users.")
        except Exception as e:
            logging.error(f"Cannot access STAFF_CHAT_ID {config.STAFF_CHAT_ID}: {e}")
    except Exception:
        logging.exception("Startup environment check failed")

if __name__ == "__main__":
    async def main():
        bot = Bot(token=config.BOT_TOKEN)
        await on_startup(bot)
        bot_info = await bot.get_me()
        logging.info(f"Bot @{bot_info.username} started")
        await dp.start_polling(bot, allowed_updates=["message", "callback_query", "chat_join_request"])
    
    asyncio.run(main())
