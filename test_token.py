import os
from dotenv import load_dotenv
from aiogram import Bot

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
print(f"Token: {BOT_TOKEN}")

if not BOT_TOKEN:
    print("No token")
    exit(1)

try:
    bot = Bot(token=BOT_TOKEN)
    print("Bot created successfully")
except Exception as e:
    print(f"Error creating bot: {e}")

# Test get_me
import asyncio

async def test():
    try:
        bot_info = await bot.get_me()
        print(f"Bot info: @{bot_info.username}")
    except Exception as e:
        print(f"Error getting bot info: {e}")

asyncio.run(test())
