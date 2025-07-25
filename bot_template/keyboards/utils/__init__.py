from aiogram import types

from bot_template.keyboards.utils.mixins import KeyboardMarkupMixin
from bot_template.keyboards.utils.payment import get_pay_text

__all__ = ("KeyboardMarkupMixin", "get_pay_text", "get_button_text")


def get_button_text(call: types.CallbackQuery, callback_data: str) -> str:
    """Get text from callback button by it's data

    Args:
        call (types.CallbackQuery): Callback query object
        callback_data (str): Callback button's data

    Returns:
        str: Callback button's text
    """
    if not call.message.reply_markup:  # type: ignore
        return ""
    for row in call.message.reply_markup.inline_keyboard:  # type: ignore
        for button in row:
            if button.callback_data == callback_data:
                return button.text
    return ""
