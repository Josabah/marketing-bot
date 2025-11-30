from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def campaign_keyboard(share_url: str, bot_link: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Share to Group", url=share_url)],
            [
                InlineKeyboardButton(text="Participate in Challenge", url=bot_link),
                InlineKeyboardButton(text="Contact Support", callback_data="contact_support")
            ],
            [
                InlineKeyboardButton(text="Submit Screenshot", callback_data="noop"),
                InlineKeyboardButton(text="My Stats", callback_data="my_stats")
            ]
        ]
    )
    return kb
