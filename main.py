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

async def on_startup():
    await init_db()
    logging.info("DB initialized")

if __name__ == "__main__":
    async def main():
        bot = Bot(token=config.BOT_TOKEN)
        await on_startup()
        bot_info = await bot.get_me()
        logging.info(f"Bot @{bot_info.username} started")
        await dp.start_polling(bot, allowed_updates=["message", "callback_query", "chat_join_request"])
    
    asyncio.run(main())
