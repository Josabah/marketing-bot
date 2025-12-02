from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

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

# Persistent chat menu (always visible at bottom, one tap away)
def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Share to Group"), KeyboardButton(text="My Stats")],
            [KeyboardButton(text="Contact Support"), KeyboardButton(text="Submit Screenshot")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Write a message..."
    )
