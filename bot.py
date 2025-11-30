# bot.py
import os
import logging
import asyncio
import re
import aiosqlite
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from urllib.parse import quote_plus
import db
from datetime import datetime

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
STAFF_CHAT_ID = os.getenv("STAFF_CHAT_ID")

# Validate required environment variables
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required. Please set it in your .env file.")
if not CHANNEL_ID:
    raise ValueError("CHANNEL_ID environment variable is required. Please set it in your .env file.")
if not STAFF_CHAT_ID:
    raise ValueError("STAFF_CHAT_ID environment variable is required. Please set it in your .env file.")

try:
    CHANNEL_ID = int(CHANNEL_ID)
    STAFF_CHAT_ID = int(STAFF_CHAT_ID)
except ValueError as e:
    raise ValueError(f"CHANNEL_ID and STAFF_CHAT_ID must be valid integers. Error: {e}")
JOIN_REQUESTS_ENABLED = os.getenv("JOIN_REQUESTS_ENABLED", "yes").lower() == "yes"
CAMPAIGN_HEADER = os.getenv("CAMPAIGN_HEADER", "🎯 Havan Academy Challenge\n\n📊 Your Stats:\n👥 Total Invited: {}\n🏆 Your Rank: {}")

# Full Amharic text for sharing
SHARE_BODY = os.getenv("SHARE_BODY")
if not SHARE_BODY:
    SHARE_BODY = (
        "ወሳኝ ነገር Online ለሆናችሁ ፍሬሽማን ተማሪዎች🎉\n\n"
        "ዩኒቨርስቲ ላይ GPA four ማምጣት በጣም ቀላል ነው። ፍሬሽማንን በስኬት አጠናቀው የፈለጉት ዲፓርትመንት የሚገቡ ልጆች ሌት እና ቀን የሚያጠኑት ብቻ አይደሉም።  "
        "ዩኒቨርስቲ ላይ ፈተና ይደጋገማል።ይሄ ማንም የሚያውቀው ነገር ነው ነገር ግን የተደራጁ ፈተናዎችን ማግኘት አስቸጋሪ ከመሆኑ የተነሳ "
        "ሳናስበው ጥያቄዎችን ሳንሰራ እንገባለን። ትልቅ ስህተት!😨\n\n"
        "የዚህ አመት ፍሬሽማኖች በጣም እድለኞች ናችሁ። ሃቫን  በቴሌግራም ላይ የተበተኑትን የmid እና የfinal exam ፈተናዎች "
        "በዩኒቨርስቲ፣ በsubject እና በአመተ ምህረት አደራጅተን እየለቀቅን ነው። 💪\n\n"
        "ከ34.8 ሺ በላይ የፍሬሽማን ተማሪዎች በሚከተሉት የቴሌግራም ቻናላችን ላይ ሁሉንም በነጻ ታገኛላችሁ።👇👇👇\n\n"
        "👉<INVITE_LINK>👆👆\n\n"
        "ከዛሬ ውጭ ሊንኩ አይሰራላችሁም። አሁኑኑ Join በሉ።"
    )

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Initialize DB on startup
async def on_startup():
    await db.init_db()
    logging.info("DB initialized")

async def make_or_get_invite(tg_user_id, user_fullname):
    # Check DB first
    link = await db.get_invite_by_user(tg_user_id)
    if link:
        return link

    # Create invite link via API
    # create_chat_invite_link requires the bot to be admin in the channel
    name = f"user_{tg_user_id}"
    try:
        params = {
            "chat_id": CHANNEL_ID,
            "name": name,
        }
        # If join requests desired, set creates_join_request
        if JOIN_REQUESTS_ENABLED:
            params["creates_join_request"] = True
        res = await bot.create_chat_invite_link(**params)
        invite_link = res.invite_link
        await db.save_invite_link(invite_link, tg_user_id)
        return invite_link
    except Exception as e:
        logging.exception("Failed creating invite link: %s", e)
        return None

async def build_share_url(invite_link, share_text):
    # Embed invite_link into the share_text (replace placeholder <INVITE_LINK> if present)
    body = share_text.replace("<INVITE_LINK>", invite_link)
    # Get bot link to add at the end
    bot_link = await get_bot_link()
    
    # Add "Participate in a challenge: <Bot Link>" at the end
    if bot_link:
        body += f"\n\nParticipate in a challenge: {bot_link}"
    
    # Telegram share deeplink - only text, no URL parameter (removed bot link from URL param)
    u = f"https://t.me/share/url?text={quote_plus(body)}"
    return u

def campaign_keyboard(share_url):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Share to Group", url=share_url)],
            [
                InlineKeyboardButton(text="Submit Screenshot", callback_data="noop"),
                InlineKeyboardButton(text="Contact Support", callback_data="contact_support")
            ],
            [InlineKeyboardButton(text="My Stats", callback_data="my_stats")]
        ]
    )
    return kb

async def get_bot_link():
    """Get the bot's Telegram link"""
    try:
        bot_info = await bot.get_me()
        return f"https://t.me/{bot_info.username}" if bot_info.username else ""
    except:
        return ""

async def get_or_create_user_topic(tg_user_id, username=None, first_name=None):
    """
    Get or create a forum topic for a user in the staff chat.
    Returns topic_id if successful, None otherwise.
    Prevents duplicate topics by checking database first.
    """
    try:
        # Check if user already has a topic in database
        existing_topic_id = await db.get_user_topic(tg_user_id)
        if existing_topic_id:
            logging.debug(f"User {tg_user_id} already has topic {existing_topic_id}")
            return existing_topic_id
        
        # Create a new topic for this user
        topic_name = f"{first_name or 'User'} (@{username})" if username else f"User {tg_user_id}"
        if len(topic_name) > 128:  # Telegram topic name limit
            topic_name = topic_name[:125] + "..."
        
        try:
            # Try to create a forum topic
            result = await bot.create_forum_topic(
                chat_id=STAFF_CHAT_ID,
                name=topic_name
            )
            topic_id = result.message_thread_id
            
            # Double-check: verify no other user has this topic (race condition protection)
            existing_user = await db.get_user_by_topic(topic_id)
            if existing_user:
                logging.warning(f"Topic {topic_id} already exists for user {existing_user}, not creating duplicate")
                return topic_id  # Return existing topic instead of creating duplicate
            
            # Save to database
            await db.save_user_topic(tg_user_id, topic_id, topic_name)
            logging.info(f"✅ Created forum topic {topic_id} ({topic_name}) for user {tg_user_id}")
            return topic_id
        except Exception as e:
            error_msg = str(e).lower()
            # Check if error is due to duplicate topic name or other issues
            if "duplicate" in error_msg or "already exists" in error_msg:
                logging.warning(f"Topic with name '{topic_name}' may already exist. Checking database...")
                # Try to find existing topic by checking all topics (if possible)
                # For now, just log and return None - user will use existing topic on next message
                return None
            # If forum topics are not available, log and return None
            logging.warning(f"Could not create forum topic (staff chat may not be a forum): {e}")
            return None
    except Exception as e:
        logging.exception(f"Error getting/creating user topic: {e}")
        return None

async def forward_to_staff_topic(message: types.Message, topic_id=None):
    """
    Forward any type of message content to staff chat (optionally to a specific topic).
    Handles: text, photo, video, voice, audio, document, animation, sticker, video_note, etc.
    """
    try:
        user_info = f"From: @{message.from_user.username or 'unknown'} (ID: {message.from_user.id})"
        if message.from_user.first_name:
            user_info += f" - {message.from_user.first_name}"
        
        # Prepare message_thread_id if topic is available
        message_thread_id = topic_id if topic_id else None
        
        # Handle different message types
        if message.text:
            # Plain text message
            text_content = f"{user_info}\n\n{message.text}"
            await bot.send_message(
                STAFF_CHAT_ID,
                text_content,
                message_thread_id=message_thread_id
            )
        elif message.photo:
            # Photo with optional caption
            caption = f"{user_info}\n\n{message.caption}" if message.caption else user_info
            await bot.send_photo(
                STAFF_CHAT_ID,
                message.photo[-1].file_id,  # Highest resolution
                caption=caption,
                message_thread_id=message_thread_id
            )
        elif message.video:
            # Video with optional caption
            caption = f"{user_info}\n\n{message.caption}" if message.caption else user_info
            await bot.send_video(
                STAFF_CHAT_ID,
                message.video.file_id,
                caption=caption,
                message_thread_id=message_thread_id
            )
        elif message.voice:
            # Voice message with optional caption
            caption = f"{user_info}\n\n{message.caption}" if message.caption else user_info
            await bot.send_voice(
                STAFF_CHAT_ID,
                message.voice.file_id,
                caption=caption,
                message_thread_id=message_thread_id
            )
        elif message.audio:
            # Audio file with optional caption
            caption = f"{user_info}\n\n{message.caption}" if message.caption else user_info
            await bot.send_audio(
                STAFF_CHAT_ID,
                message.audio.file_id,
                caption=caption,
                message_thread_id=message_thread_id
            )
        elif message.document:
            # Document with optional caption
            caption = f"{user_info}\n\n{message.caption}" if message.caption else user_info
            await bot.send_document(
                STAFF_CHAT_ID,
                message.document.file_id,
                caption=caption,
                message_thread_id=message_thread_id
            )
        elif message.animation:
            # GIF/Animation with optional caption
            caption = f"{user_info}\n\n{message.caption}" if message.caption else user_info
            await bot.send_animation(
                STAFF_CHAT_ID,
                message.animation.file_id,
                caption=caption,
                message_thread_id=message_thread_id
            )
        elif message.sticker:
            # Sticker
            await bot.send_message(
                STAFF_CHAT_ID,
                f"{user_info}\n\n[Sent a sticker]",
                message_thread_id=message_thread_id
            )
            await bot.send_sticker(
                STAFF_CHAT_ID,
                message.sticker.file_id,
                message_thread_id=message_thread_id
            )
        elif message.video_note:
            # Video note (round video)
            await bot.send_message(
                STAFF_CHAT_ID,
                f"{user_info}\n\n[Sent a video note]",
                message_thread_id=message_thread_id
            )
            await bot.send_video_note(
                STAFF_CHAT_ID,
                message.video_note.file_id,
                message_thread_id=message_thread_id
            )
        elif message.contact:
            # Contact
            await bot.send_contact(
                STAFF_CHAT_ID,
                phone_number=message.contact.phone_number,
                first_name=message.contact.first_name,
                last_name=message.contact.last_name,
                message_thread_id=message_thread_id
            )
            await bot.send_message(
                STAFF_CHAT_ID,
                f"{user_info}\n\n[Sent a contact]",
                message_thread_id=message_thread_id
            )
        elif message.location:
            # Location
            await bot.send_location(
                STAFF_CHAT_ID,
                latitude=message.location.latitude,
                longitude=message.location.longitude,
                message_thread_id=message_thread_id
            )
            await bot.send_message(
                STAFF_CHAT_ID,
                f"{user_info}\n\n[Sent a location]",
                message_thread_id=message_thread_id
            )
        elif message.forward_from or message.forward_from_chat:
            # Forwarded message - try to forward it
            try:
                await message.forward(STAFF_CHAT_ID, message_thread_id=message_thread_id)
                await bot.send_message(
                    STAFF_CHAT_ID,
                    f"{user_info}\n\n[Forwarded message]",
                    message_thread_id=message_thread_id
                )
            except Exception as e:
                logging.warning(f"Could not forward message: {e}")
                await bot.send_message(
                    STAFF_CHAT_ID,
                    f"{user_info}\n\n[Could not forward message - content may be protected]",
                    message_thread_id=message_thread_id
                )
        else:
            # Unknown content type - send info message
            await bot.send_message(
                STAFF_CHAT_ID,
                f"{user_info}\n\n[Sent unsupported content type]",
                message_thread_id=message_thread_id
            )
        
        return True
    except Exception as e:
        logging.exception(f"Error forwarding message to staff: {e}")
        return False

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    tg_id = message.from_user.id
    await db.ensure_user(tg_id, message.from_user.username, message.from_user.first_name)
    # create invite link
    invite_link = await make_or_get_invite(tg_id, f"{message.from_user.first_name or ''}")
    if not invite_link:
        await message.reply("Error creating invite link. Please contact support.")
        return

    # compute stats - only counts joins via bot-created invite links
    total_invites = await db.get_user_join_count(tg_id)
    rank, total = await db.get_rank(tg_id)
    # Prepare header
    header = CAMPAIGN_HEADER.format(total_invites, rank or "-")
    # Build the composed share text by inserting invite link into SHARE_BODY
    composed = SHARE_BODY.replace("<INVITE_LINK>", invite_link)
    share_url = await build_share_url(invite_link, composed)
    kb = campaign_keyboard(share_url)
    # Show full message text above buttons (no truncation)
    await message.reply(header + "\n\n" + composed, reply_markup=kb)

@dp.callback_query(lambda c: c.data == "my_stats")
async def cb_my_stats(query: types.CallbackQuery):
    tg_id = query.from_user.id
    await db.ensure_user(tg_id, query.from_user.username, query.from_user.first_name)
    count = await db.get_user_join_count(tg_id)
    rank, total = await db.get_rank(tg_id)
    rank_text = f"{rank}/{total}" if rank else f"Unranked (0/{total})"
    text = f"Your stats:\nTotal invited (via your link): {count}\nRank: {rank_text}"
    # Keep buttons visible - edit the original message to show stats, preserving buttons
    try:
        await query.message.edit_text(text, reply_markup=query.message.reply_markup)
    except:
        # If edit fails, send new message but keep original with buttons
        await query.message.answer(text)
    await query.answer()

@dp.callback_query(lambda c: c.data == "contact_support")
async def cb_contact(query: types.CallbackQuery):
    # Keep buttons visible - send new message, original message with buttons stays
    await query.message.answer("Send us your question or anything related to the challenge and staff will reply. Just send it as a normal message here.")
    await query.answer()
    
@dp.callback_query(lambda c: c.data == "noop")
async def cb_noop(query: types.CallbackQuery):
    """No-op handler for buttons that don't need action"""
    await query.answer("You can send media files & screenshots directly to this chat to submit proof.", show_alert=True)

async def forward_staff_message_to_user(message: types.Message, user_id: int):
    """
    Forward staff message from topic to the user.
    Handles all content types: text, media, voice, etc.
    """
    try:
        # Check if message is from bot itself (skip)
        if message.from_user and message.from_user.is_bot:
            return False
        
        # Handle different message types
        if message.text:
            # Plain text message
            await bot.send_message(user_id, f"💬 Staff: {message.text}")
        elif message.photo:
            # Photo with optional caption
            caption = message.caption or ""
            await bot.send_photo(user_id, message.photo[-1].file_id, caption=caption)
        elif message.video:
            # Video with optional caption
            caption = message.caption or ""
            await bot.send_video(user_id, message.video.file_id, caption=caption)
        elif message.voice:
            # Voice message with optional caption
            caption = message.caption or ""
            await bot.send_voice(user_id, message.voice.file_id, caption=caption)
        elif message.audio:
            # Audio file with optional caption
            caption = message.caption or ""
            await bot.send_audio(user_id, message.audio.file_id, caption=caption)
        elif message.document:
            # Document with optional caption
            caption = message.caption or ""
            await bot.send_document(user_id, message.document.file_id, caption=caption)
        elif message.animation:
            # GIF/Animation with optional caption
            caption = message.caption or ""
            await bot.send_animation(user_id, message.animation.file_id, caption=caption)
        elif message.sticker:
            # Sticker
            await bot.send_sticker(user_id, message.sticker.file_id)
        elif message.video_note:
            # Video note (round video)
            await bot.send_video_note(user_id, message.video_note.file_id)
        elif message.contact:
            # Contact
            await bot.send_contact(
                user_id,
                phone_number=message.contact.phone_number,
                first_name=message.contact.first_name,
                last_name=message.contact.last_name
            )
        elif message.location:
            # Location
            await bot.send_location(
                user_id,
                latitude=message.location.latitude,
                longitude=message.location.longitude
            )
        elif message.forward_from or message.forward_from_chat:
            # Forwarded message - try to forward it
            try:
                await message.forward(user_id)
            except Exception as e:
                logging.warning(f"Could not forward message to user: {e}")
                await bot.send_message(user_id, "📎 [Staff forwarded a message that couldn't be forwarded]")
        else:
            # Unknown content type
            await bot.send_message(user_id, "📎 Staff sent a message (unsupported content type)")
        
        return True
    except Exception as e:
        logging.exception(f"Error forwarding staff message to user {user_id}: {e}")
        return False

@dp.message(F.chat.id == STAFF_CHAT_ID)
async def handle_staff_chat_messages(message: types.Message):
    """
    Handle messages from staff in the staff chat (especially in forum topics).
    Forward staff messages from topics back to users.
    """
    # Skip if message is from bot itself
    if message.from_user and message.from_user.is_bot:
        return
    
    # Skip /reply command (handled separately)
    if message.text and message.text.startswith('/reply'):
        return
    
    # In aiogram 3.x, message_thread_id should be directly accessible on the message object
    # Try the most direct approach first
    topic_id = None
    
    # Method 1: Direct attribute access (standard in aiogram 3.x)
    # In aiogram 3.x, messages in forum topics have message_thread_id directly accessible
    try:
        topic_id = message.message_thread_id if hasattr(message, 'message_thread_id') else None
        if topic_id:
            logging.info(f"✅ Found topic_id: {topic_id} (direct access)")
    except AttributeError:
        pass
    
    # Method 2: Check via model_dump if direct access didn't work (Pydantic model)
    if not topic_id and hasattr(message, 'model_dump'):
        try:
            msg_dict = message.model_dump()
            topic_id = msg_dict.get('message_thread_id')
            if topic_id:
                logging.info(f"✅ Found topic_id: {topic_id} (via model_dump)")
        except Exception as e:
            logging.debug(f"Error in model_dump: {e}")
    
    # Method 3: Check reply_to_message if it's a reply (replies inherit the topic)
    if not topic_id and message.reply_to_message:
        try:
            topic_id = message.reply_to_message.message_thread_id if hasattr(message.reply_to_message, 'message_thread_id') else None
            if topic_id:
                logging.info(f"✅ Found topic_id: {topic_id} (via reply_to_message)")
        except AttributeError:
            pass
    
    if topic_id:
        # Get user ID from topic
        user_id = await db.get_user_by_topic(topic_id)
        if user_id:
            # Forward staff message to user
            logging.info(f"📤 Forwarding staff message from topic {topic_id} to user {user_id} (from: @{message.from_user.username or 'unknown'})")
            success = await forward_staff_message_to_user(message, user_id)
            if success:
                logging.info(f"✅ Successfully forwarded staff message from topic {topic_id} to user {user_id}")
            else:
                logging.error(f"❌ Failed to forward staff message from topic {topic_id} to user {user_id}")
        else:
            logging.warning(f"⚠️ Message in topic {topic_id} but no user found in database for this topic. Message: {message.text[:50] if message.text else 'media'}")
    else:
        # Message in staff chat but not in a topic - log for debugging
        if message.text and not message.text.startswith('/'):
            logging.info(f"ℹ️ Message in staff chat but topic_id not found. This might be a general message.")
            logging.info(f"   Message text: {message.text[:100]}")
            logging.info(f"   Message attributes: message_thread_id={getattr(message, 'message_thread_id', 'NOT FOUND')}, thread_id={getattr(message, 'thread_id', 'NOT FOUND')}")

@dp.message()
async def handle_all_messages(message: types.Message):
    """
    Handle messages from users and staff:
    - Forward user messages to staff chat (in their topic)
    - Forward staff messages from topics back to users
    """
    # Handle messages in staff chat (from staff in topics)
    if message.chat.id == STAFF_CHAT_ID:
        # Skip if message is from bot itself
        if message.from_user and message.from_user.is_bot:
            return
        
        # Skip /reply command (handled separately)
        if message.text and message.text.startswith('/reply'):
            return
        
        # Check if message is in a topic - try multiple ways to get topic ID
        topic_id = None
        
        # Method 1: Direct attribute access (most reliable in aiogram 3.x)
        try:
            if hasattr(message, 'message_thread_id'):
                topic_id = getattr(message, 'message_thread_id', None)
                if topic_id:
                    logging.info(f"✅ Found topic_id via message.message_thread_id: {topic_id}")
        except Exception as e:
            logging.debug(f"Error accessing message_thread_id: {e}")
        
        # Method 2: Check via model_dump (Pydantic model)
        if not topic_id:
            try:
                if hasattr(message, 'model_dump'):
                    msg_dict = message.model_dump()
                    topic_id = msg_dict.get('message_thread_id')
                    if topic_id:
                        logging.info(f"✅ Found topic_id via model_dump: {topic_id}")
            except Exception as e:
                logging.debug(f"Error in model_dump: {e}")
        
        # Method 3: Check if message is a reply in a topic thread
        if not topic_id and message.reply_to_message:
            try:
                if hasattr(message.reply_to_message, 'message_thread_id'):
                    topic_id = getattr(message.reply_to_message, 'message_thread_id', None)
                    if topic_id:
                        logging.info(f"✅ Found topic_id via reply_to_message.message_thread_id: {topic_id}")
            except Exception as e:
                logging.debug(f"Error accessing reply_to_message.message_thread_id: {e}")
        
        # Method 3.5: Try accessing via raw Telegram API response
        if not topic_id:
            try:
                # In aiogram 3.x, sometimes we need to check the raw data
                if hasattr(message, 'model_fields_set'):
                    # Try to get from the message's internal representation
                    for field_name in ['message_thread_id', 'thread_id']:
                        if hasattr(message, field_name):
                            val = getattr(message, field_name, None)
                            if val:
                                topic_id = val
                                logging.info(f"✅ Found topic_id via {field_name}: {topic_id}")
                                break
            except Exception as e:
                logging.debug(f"Error in field access: {e}")
        
        # Method 4: Try dict access (fallback)
        if not topic_id:
            try:
                if isinstance(message, dict) or hasattr(message, '__dict__'):
                    msg_dict = dict(message) if isinstance(message, dict) else message.__dict__
                    topic_id = msg_dict.get('message_thread_id') or msg_dict.get('thread_id')
                    if topic_id:
                        logging.info(f"✅ Found topic_id via dict access: {topic_id}")
            except Exception as e:
                logging.debug(f"Error in dict access: {e}")
        
        # Method 5: Check thread_id attribute (alternative name)
        if not topic_id:
            try:
                if hasattr(message, 'thread_id'):
                    topic_id = getattr(message, 'thread_id', None)
                    if topic_id:
                        logging.info(f"✅ Found topic_id via thread_id: {topic_id}")
            except Exception as e:
                logging.debug(f"Error accessing thread_id: {e}")
        
        if topic_id:
            # Get user ID from topic
            user_id = await db.get_user_by_topic(topic_id)
            if user_id:
                # Forward staff message to user
                logging.info(f"📤 Forwarding staff message from topic {topic_id} to user {user_id} (from: @{message.from_user.username or 'unknown'})")
                success = await forward_staff_message_to_user(message, user_id)
                if success:
                    logging.info(f"✅ Successfully forwarded staff message from topic {topic_id} to user {user_id}")
                else:
                    logging.error(f"❌ Failed to forward staff message from topic {topic_id} to user {user_id}")
            else:
                logging.warning(f"⚠️ Message in topic {topic_id} but no user found in database for this topic. Message: {message.text[:50] if message.text else 'media'}")
        else:
            # Message in staff chat but not in a topic - log for debugging
            if message.text and not message.text.startswith('/'):
                logging.info(f"ℹ️ Message in staff chat but topic_id not found. This might be a general message.")
                logging.info(f"   Message text: {message.text[:100]}")
                logging.info(f"   Message attributes: message_thread_id={getattr(message, 'message_thread_id', 'NOT FOUND')}, thread_id={getattr(message, 'thread_id', 'NOT FOUND')}")
                # Try to inspect the message object
                try:
                    if hasattr(message, 'model_dump'):
                        msg_dict = message.model_dump()
                        logging.info(f"   Available keys in model_dump: {list(msg_dict.keys())[:20]}")
                except:
                    pass
        return
    
    # Handle messages from users (private chat)
    if message.chat.type != "private":
        return

    # Ignore commands (handled by other handlers)
    if message.text and message.text.startswith('/'):
        return

    tg_id = message.from_user.id
    await db.ensure_user(tg_id, message.from_user.username, message.from_user.first_name)

    # Get or create forum topic for this user
    topic_id = await get_or_create_user_topic(
        tg_id,
        message.from_user.username,
        message.from_user.first_name
    )

    # Forward all content types to staff chat (with topic if available)
    success = await forward_to_staff_topic(message, topic_id)
    
    if success:
        # Acknowledge to user
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

@dp.chat_join_request()
async def handle_join_request(update: types.ChatJoinRequest):
    """
    When join requests arrive, only record joins via invite links created by this bot.
    Only links stored in our database (bot-created) will be counted in stats.
    """
    try:
        invite_link = None
        # Try multiple ways to get the invite link (aiogram 3.x compatibility)
        if hasattr(update, 'invite_link') and update.invite_link:
            if hasattr(update.invite_link, 'invite_link'):
                invite_link = update.invite_link.invite_link
            elif isinstance(update.invite_link, str):
                invite_link = update.invite_link
        
        joining_user = update.from_user.id
        
        # Only record joins via invite links created by this bot (stored in our database)
        # This ensures stats only include users who joined via bot-created links, not admin-created ones
        new_join_recorded = False
        if invite_link:
            # Verify this invite link exists in our database before recording
            existing_link = await db.get_invite_by_link(invite_link)
            if existing_link:
                # Check if this join was already recorded (avoid duplicates)
                async with aiosqlite.connect(db.DB_PATH) as conn:
                    cur = await conn.execute(
                        "SELECT id FROM join_events WHERE invite_link = ? AND joined_user_id = ?",
                        (invite_link, joining_user)
                    )
                    existing_join = await cur.fetchone()
                    if not existing_join:
                        await db.record_join(invite_link, joining_user)
                        new_join_recorded = True
                        logging.info(f"✅ Recorded join for user {joining_user} via bot-created link {invite_link[:30]}...")
                    else:
                        logging.info(f"⚠️ Join for user {joining_user} already recorded, skipping duplicate")
            else:
                logging.info(f"❌ Ignoring join from user {joining_user} via non-bot invite link (created by other admin)")
        else:
            logging.warning(f"⚠️ No invite link found in join request from user {joining_user}")
        
        # Approve the join request automatically
        await bot.approve_chat_join_request(chat_id=CHANNEL_ID, user_id=joining_user)
        
        # Notify staff only for bot-created links when a new join is recorded
        if new_join_recorded and invite_link:
            await bot.send_message(STAFF_CHAT_ID, f"✅ User {update.from_user.id} joined via bot invite link. Auto-approved and logged.")
    except Exception as e:
        logging.exception("Error handling join request: %s", e)
        await bot.send_message(STAFF_CHAT_ID, f"Error handling join request: {e}")

# Staff helper: /reply -> staff replies to user messages
@dp.message(Command("reply"))
async def staff_reply(msg: types.Message):
    # Only allow in staff chat
    if msg.chat.id != STAFF_CHAT_ID:
        return
    # staff should reply to a user's message
    if not msg.reply_to_message:
        await msg.reply("Use this command as a reply to a user's message in staff chat. Example: /reply <your message>")
        return
    
    # Try to extract user ID from the replied message
    text = msg.reply_to_message.text or msg.reply_to_message.caption or ""
    tg_id = None
    
    # Try to parse ID from message text (format: "From: @username (ID: 123456)")
    m = re.search(r"ID:\s*(\d+)", text, re.IGNORECASE)
    if m:
        tg_id = int(m.group(1))
    else:
        # Try alternative format: "id:123456"
        m = re.search(r"id:\s*(\d+)", text, re.IGNORECASE)
        if m:
            tg_id = int(m.group(1))
    
    if not tg_id:
        await msg.reply("Could not find user ID in the replied message. Make sure you reply to a message from a user.")
        return
    
    # Build reply content: take staff message text minus the /reply command
    if not msg.text:
        await msg.reply("No reply text provided. Usage: /reply <your message>")
        return
    parts = msg.text.split(None, 1)
    content = parts[1] if len(parts) > 1 else ""
    if not content:
        await msg.reply("No reply text provided. Usage: /reply <your message>")
        return
    
    try:
        await bot.send_message(tg_id, f"Staff reply: {content}")
        await msg.reply("✅ Sent to user.")
    except Exception as e:
        logging.exception(f"Error sending reply to user {tg_id}: {e}")
        await msg.reply(f"❌ Error sending message to user: {e}")

# Staff command to export submissions
@dp.message(Command("export_submissions"))
async def export_submissions(msg: types.Message):
    if msg.chat.id != STAFF_CHAT_ID:
        return
    import aiosqlite
    out = []
    async with aiosqlite.connect(db.DB_PATH) as conn:
        cur = await conn.execute(
            "SELECT id, tg_user_id, file_ids, caption, created_at, staff_handled FROM submissions ORDER BY created_at DESC LIMIT 50"
        )
        rows = await cur.fetchall()
        for r in rows:
            out.append(f"{r[0]} | user:{r[1]} | files:{r[2]} | caption:{r[3]} | at:{r[4]} | handled:{r[5]}")
    await msg.reply("\n".join(out) if out else "no submissions")

if __name__ == "__main__":
    async def main():
        await on_startup()
        # Fetch bot info to get username
        bot_info = await bot.get_me()
        logging.info(f"Bot @{bot_info.username} started")
        await dp.start_polling(bot, allowed_updates=["message", "callback_query", "chat_join_request"])
    
    asyncio.run(main())
