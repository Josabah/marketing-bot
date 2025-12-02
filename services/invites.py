from aiogram import Bot
from config import config
from db.repository import get_invite_by_user, save_invite_link
import logging
from urllib.parse import quote_plus
from services.forwarding import get_bot_link

async def make_or_get_invite(bot: Bot, tg_user_id: int, user_fullname: str) -> str:
    link = await get_invite_by_user(tg_user_id)
    if link:
        return link

    try:
        # Always try to create a unique invite link
        params = {
            "chat_id": config.CHANNEL_ID,
            "name": f"user_{tg_user_id}",
        }
        if config.JOIN_REQUESTS_ENABLED:
            params["creates_join_request"] = True
        res = await bot.create_chat_invite_link(**params)
        invite_link = res.invite_link
        await save_invite_link(invite_link, tg_user_id)
        return invite_link
    except Exception as e:
        logging.warning(f"Failed to create invite link for {tg_user_id}: {e}")
        # Do not save or use a shared/public link here to avoid breaking tracking
        return None

async def build_share_url(bot: Bot, invite_link: str, share_text: str) -> str:
    body = share_text.replace("<INVITE_LINK>", invite_link)
    bot_link = await get_bot_link(bot)
    if bot_link:
        body += f"\n\nParticipate in a challenge: {bot_link}"
    u = f"https://t.me/share/url?text={quote_plus(body)}"
    return u
