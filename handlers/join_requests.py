from aiogram import Router, types
from config import config
from db.repository import get_invite_by_link, record_join, DB_PATH
import aiosqlite
import logging

router = Router()

@router.chat_join_request()
async def handle_join_request(update: types.ChatJoinRequest):
    try:
        # Always approve to avoid blocking users, even if DB fails
        joining_user = update.from_user.id
        try:
            await update.bot.approve_chat_join_request(chat_id=config.CHANNEL_ID, user_id=joining_user)
        except Exception as approve_err:
            logging.exception("Failed to approve join request: %s", approve_err)
            # Do not return; still attempt to record join for stats

        invite_link = None
        if hasattr(update, 'invite_link') and update.invite_link:
            if hasattr(update.invite_link, 'invite_link'):
                invite_link = update.invite_link.invite_link
            elif isinstance(update.invite_link, str):
                invite_link = update.invite_link

        new_join_recorded = False
        if invite_link:
            existing_link = await get_invite_by_link(invite_link)
            if existing_link:
                async with aiosqlite.connect(DB_PATH) as conn:
                    cur = await conn.execute(
                        "SELECT id FROM join_events WHERE invite_link = ? AND joined_user_id = ?",
                        (invite_link, joining_user)
                    )
                    existing_join = await cur.fetchone()
                    if not existing_join:
                        await record_join(invite_link, joining_user)
                        new_join_recorded = True

        if new_join_recorded:
            try:
                await update.bot.send_message(config.STAFF_CHAT_ID, f"✅ User {joining_user} joined via bot invite link. Auto-approved.")
            except Exception:
                logging.debug("Could not notify staff about new join")
    except Exception as e:
        logging.exception("Error handling join request: %s", e)
