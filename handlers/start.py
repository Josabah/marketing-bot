from aiogram import Router, types
from aiogram.filters import Command
from config import config
from db.repository import ensure_user, get_user_join_count, get_rank
from services.invites import make_or_get_invite, build_share_url
from services.forwarding import get_bot_link
from keyboards.campaign import campaign_keyboard
import logging

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    try:
        tg_id = message.from_user.id
        await ensure_user(tg_id, message.from_user.username, message.from_user.first_name)
        
        # Try to create/get invite link
        invite_link = await make_or_get_invite(message.bot, tg_id, f"{message.from_user.first_name or ''}")
        if not invite_link:
            logging.warning(f"Failed to create invite link for {tg_id}, using fallback")
            # Fallback: Use channel URL if possible
            try:
                chat = await message.bot.get_chat(config.CHANNEL_ID)
                invite_link = f"https://t.me/{chat.username}" if chat.username else "https://t.me/joinchat/..."  # Placeholder
            except:
                invite_link = "https://t.me/your_channel"  # Generic fallback
        
        # Compute stats
        total_invites = await get_user_join_count(tg_id)
        rank, total = await get_rank(tg_id)
        header = config.CAMPAIGN_HEADER.format(total_invites, rank or "-")
        composed = config.SHARE_BODY.replace("<INVITE_LINK>", invite_link)
        
        # Build and send with keyboard
        share_url = await build_share_url(message.bot, invite_link, composed)
        bot_link = await get_bot_link(message.bot)
        kb = campaign_keyboard(share_url, bot_link)
        await message.reply(header + "\n\n" + composed, reply_markup=kb)
        
    except Exception as e:
        logging.error(f"Error in start for {tg_id}: {e}")
        await message.reply("An error occurred. Please try again or contact support.")
