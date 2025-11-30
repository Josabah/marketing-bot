#!/usr/bin/env python3
"""Test script to verify bot credentials and Telegram connectivity"""
import asyncio
import sys
from aiogram import Bot
from aiogram.exceptions import TelegramUnauthorizedError, TelegramBadRequest

import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "7984352639:AAEaAf346Jt5Kltm_VJnXFIzLAMBilHvWfE")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "-1002055207822"))
STAFF_CHAT_ID = int(os.getenv("STAFF_CHAT_ID", "-1003221684202"))

async def test_bot():
    print("🔍 Testing bot credentials...\n")
    
    try:
        bot = Bot(token=BOT_TOKEN)
        
        # Test 1: Verify bot token is valid
        print("1. Testing bot token...")
        try:
            bot_info = await bot.get_me()
            print(f"   ✅ Bot token is VALID")
            print(f"   📋 Bot username: @{bot_info.username}")
            print(f"   📋 Bot ID: {bot_info.id}")
            print(f"   📋 Bot name: {bot_info.first_name}")
        except TelegramUnauthorizedError:
            print(f"   ❌ Bot token is INVALID or has been revoked")
            return False
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
        
        # Test 2: Check if bot can access the channel
        print(f"\n2. Testing channel access (ID: {CHANNEL_ID})...")
        try:
            chat_info = await bot.get_chat(CHANNEL_ID)
            print(f"   ✅ Channel accessible")
            print(f"   📋 Channel title: {chat_info.title}")
            print(f"   📋 Channel type: {chat_info.type}")
            
            # Check if bot is admin
            try:
                member = await bot.get_chat_member(CHANNEL_ID, bot_info.id)
                if member.status in ['administrator', 'creator']:
                    print(f"   ✅ Bot IS an admin in the channel")
                else:
                    print(f"   ⚠️  Bot is NOT an admin (status: {member.status})")
                    print(f"   ⚠️  The bot needs admin rights to create invite links!")
            except Exception as e:
                print(f"   ⚠️  Could not check admin status: {e}")
                
        except TelegramBadRequest as e:
            print(f"   ❌ Cannot access channel: {e}")
            print(f"   ❌ Possible reasons:")
            print(f"      - Channel ID is incorrect")
            print(f"      - Bot is not a member of the channel")
            print(f"      - Bot was removed from the channel")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Test 3: Check if bot can access the staff chat
        print(f"\n3. Testing staff chat access (ID: {STAFF_CHAT_ID})...")
        try:
            chat_info = await bot.get_chat(STAFF_CHAT_ID)
            print(f"   ✅ Staff chat accessible")
            print(f"   📋 Chat title: {chat_info.title if hasattr(chat_info, 'title') else 'Private Chat'}")
            print(f"   📋 Chat type: {chat_info.type}")
        except TelegramBadRequest as e:
            print(f"   ❌ Cannot access staff chat: {e}")
            print(f"   ❌ Possible reasons:")
            print(f"      - Staff chat ID is incorrect")
            print(f"      - Bot is not a member of the staff chat")
            print(f"      - Bot was removed from the staff chat")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Test 4: Try to create an invite link (if bot is admin)
        print(f"\n4. Testing invite link creation...")
        try:
            invite = await bot.create_chat_invite_link(
                chat_id=CHANNEL_ID,
                name="test_link"
            )
            print(f"   ✅ Can create invite links")
            print(f"   📋 Test invite link: {invite.invite_link}")
        except TelegramBadRequest as e:
            print(f"   ❌ Cannot create invite link: {e}")
            if "not enough rights" in str(e).lower() or "administrator" in str(e).lower():
                print(f"   ❌ The bot needs admin rights with 'Invite users via link' permission!")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        await bot.session.close()
        
        print(f"\n✅ Credential check complete!")
        return True
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        result = asyncio.run(test_bot())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)

