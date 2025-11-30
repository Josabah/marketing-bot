from aiogram import Router, types
from config import config
from db.repository import ensure_user, get_user_join_count, get_rank

router = Router()

@router.callback_query(lambda c: c.data == "my_stats")
async def cb_my_stats(query: types.CallbackQuery):
    tg_id = query.from_user.id
    await ensure_user(tg_id, query.from_user.username, query.from_user.first_name)
    count = await get_user_join_count(tg_id)
    rank, total = await get_rank(tg_id)
    rank_text = f"{rank}/{total}" if rank else f"Unranked (0/{total})"
    text = f"Your stats:\nTotal invited (via your link): {count}\nRank: {rank_text}"
    try:
        await query.message.edit_text(text, reply_markup=query.message.reply_markup)
    except:
        await query.message.answer(text)
    await query.answer()

@router.callback_query(lambda c: c.data == "contact_support")
async def cb_contact(query: types.CallbackQuery):
    await query.message.answer("Send us your question or anything related to the challenge and staff will reply. Just send it as a normal message here.")
    await query.answer()
    
@router.callback_query(lambda c: c.data == "noop")
async def cb_noop(query: types.CallbackQuery):
    await query.answer("You can send media files & screenshots directly to this chat to submit proof.", show_alert=True)
