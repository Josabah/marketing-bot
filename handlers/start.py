from aiogram import Router, types
from aiogram.filters import Command
from config import config
from db.repository import ensure_user, get_user_join_count, get_rank
from services.invites import make_or_get_invite, build_share_url
from services.forwarding import get_bot_link
from keyboards.campaign import campaign_keyboard, main_menu_keyboard
import logging

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    try:
        tg_id = message.from_user.id
        await ensure_user(tg_id, message.from_user.username, message.from_user.first_name)
        
        # Try to create/get invite link; if it fails, stop and inform the user
        invite_link = await make_or_get_invite(message.bot, tg_id, f"{message.from_user.first_name or ''}")
        if not invite_link:
            logging.warning(f"Failed to create invite link for {tg_id}")
            await message.reply("Sorry, I couldn't create your personal invite link right now. Please try again in a minute.")
            return
        
        # Compute stats
        total_invites = await get_user_join_count(tg_id)
        rank, total = await get_rank(tg_id)
        header = config.CAMPAIGN_HEADER.format(total_invites, f"{rank}/{total}" if rank else f"0/{total}")
        composed = config.SHARE_BODY.replace("<INVITE_LINK>", invite_link)
        
        # Build and send with keyboard
        share_url = await build_share_url(message.bot, invite_link, composed)
        bot_link = await get_bot_link(message.bot)
        ikb = campaign_keyboard(share_url, bot_link)
        rkb = main_menu_keyboard()
        
        # Send the main message with inline actions, hide link preview to keep it concise
        await message.reply(header + "\n\n" + composed, reply_markup=ikb, disable_web_page_preview=True)
        
        # Then set persistent menu with an invisible character to avoid Bad Request on empty text
        try:
            await message.answer("\u2063", reply_markup=rkb)
        except Exception as e2:
            logging.debug(f"Failed to send persistent menu: {e2}")
        
    except Exception as e:
        logging.exception(f"Error in start for {message.from_user.id}: {e}")
        await message.reply("An error occurred. Please try again or contact support.")
