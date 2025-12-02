from aiogram import Router, types, F
from config import config
from db.repository import ensure_user, get_user_join_count, get_rank
from services.invites import make_or_get_invite, build_share_url
from services.topics import get_or_create_user_topic
from services.forwarding import forward_any, get_bot_link
from keyboards.campaign import main_menu_keyboard, campaign_keyboard

router = Router()

@router.message(F.chat.type == "private")
async def handle_user_messages(message: types.Message):
    # Handle persistent menu buttons first (do not forward these to staff)
    if message.text:
        text = message.text.strip()
        if text == "Share to Group":
            tg_id = message.from_user.id
            await ensure_user(tg_id, message.from_user.username, message.from_user.first_name)
            invite_link = await make_or_get_invite(message.bot, tg_id, f"{message.from_user.first_name or ''}")
            if not invite_link:
                await message.reply("Sorry, I couldn't create your personal invite link right now. Please try again in a minute.")
                return
            composed = config.SHARE_BODY.replace("<INVITE_LINK>", invite_link)
            share_url = await build_share_url(message.bot, invite_link, composed)
            bot_link = await get_bot_link(message.bot)
            ikb = campaign_keyboard(share_url, bot_link)
            # Prompt to click the inline share button below (no extra confirmations)
            await message.reply("Click the Share to Group button below to share to your class groups.", reply_markup=ikb)
            return
        if text == "My Stats":
            tg_id = message.from_user.id
            await ensure_user(tg_id, message.from_user.username, message.from_user.first_name)
            count = await get_user_join_count(tg_id)
            rank, total = await get_rank(tg_id)
            rank_text = f"{rank}/{total}" if rank else f"0/{total}"
            await message.reply(f"Your stats:\nTotal invited (via your link): {count}\nRank: {rank_text}")
            return
        if text == "Contact Support":
            await message.reply("Send your question or message here, and staff will reply.")
            return
        if text == "Submit Screenshot":
            await message.reply("You can send your screenshots or media directly here; we'll forward them to staff.")
            return
    
    # Ignore commands
    if message.text and message.text.startswith('/'):
        return

    # Default: forward user content to staff (topic-specific if available)
    tg_id = message.from_user.id
    await ensure_user(tg_id, message.from_user.username, message.from_user.first_name)

    topic_id = await get_or_create_user_topic(message.bot, tg_id, message.from_user.username, message.from_user.first_name)
    if topic_id is None:
        # Could not create or access a topic; notify user and do not spam general chat
        success = await forward_any(message.bot, message, config.STAFF_CHAT_ID, None, None)
        if not success:
            await message.reply("⚠️ There was an error forwarding your message. Please try again or contact support.")
        else:
            await message.reply("⚠️ Topic creation failed; staff received your message but thread was not created.")
        return

    # Forward into the user's topic only
    success = await forward_any(message.bot, message, config.STAFF_CHAT_ID, None, topic_id)

    if not success:
        await message.reply("⚠️ There was an error forwarding your message. Please try again or contact support.")
