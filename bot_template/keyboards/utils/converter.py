from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from loguru import logger

from bot_template.keyboards.models.base import ButtonRow
from bot_template.keyboards.models.bottom_keyboard import (
    BottomKeyboard,
    RequestContactButton,
    RequestLocationButton,
    RequestPollButton,
    TextButton,
)
from bot_template.keyboards.models.inline_keyboard import (
    CallbackButton,
    InlineKeyboard,
    SwitchInlineButton,
    SwitchInlineChosenChatButton,
    SwitchInlineCurrentChatButton,
    URLButton,
)
from bot_template.keyboards.models.multi_keyboard import WebAppButton


class KeyboardConverter:
    def __new__(
        cls, keyboard: InlineKeyboardMarkup | ReplyKeyboardMarkup | None
    ) -> InlineKeyboard | BottomKeyboard | None:
        # print(keyboard)
        if not keyboard:
            return None
        if keyboard.inline_keyboard:
            return cls.convert_inline_keyboard(keyboard)
        elif keyboard.keyboard:
            return cls.convert_reply_keyboard(keyboard)

    @staticmethod
    def convert_button(button: InlineKeyboardButton | KeyboardButton):
        context = button.__class__.__name__
        match context:
            case "InlineKeyboardButton":
                if button.url:
                    return URLButton(button.text, button.url)
                elif button.callback_data:
                    return CallbackButton(button.text, button.callback_data)
                elif button.switch_inline_query:
                    return SwitchInlineButton(
                        button.text, button.switch_inline_query
                    )
                elif button.switch_inline_query_current_chat:
                    return SwitchInlineCurrentChatButton(
                        button.text,
                        button.switch_inline_query_current_chat,
                    )
                elif button.switch_inline_query_chosen_chat:
                    return SwitchInlineChosenChatButton(
                        button.text,
                        button.switch_inline_query_chosen_chat.query,
                        button.switch_inline_query_chosen_chat.allow_user_chats,
                        button.switch_inline_query_chosen_chat.allow_bot_chats,
                        button.switch_inline_query_chosen_chat.allow_group_chats,
                        button.switch_inline_query_chosen_chat.allow_channel_chats,
                    )
                elif button.web_app:
                    return WebAppButton(button.text, button.web_app.url)
                else:
                    logger.warning(
                        f"Unsupported inline keyboard button: {button.model_dump_json()}"
                    )
                    return None
            case "KeyboardButton":
                if button.request_contact:
                    return RequestContactButton(button.text)
                elif button.request_location:
                    return RequestLocationButton(button.text)
                elif button.request_poll:
                    return RequestPollButton(
                        button.text, button.request_poll.type
                    )
                elif button.web_app:
                    return WebAppButton(button.text, button.web_app.url)
                else:
                    return TextButton(button.text)
            case _:
                raise ValueError(f"context {context} is not supported")

    @staticmethod
    def convert_inline_keyboard(
        keyboard: InlineKeyboardMarkup,
    ) -> InlineKeyboard:
        _keyboard = InlineKeyboard(
            *[
                ButtonRow(
                    *[
                        KeyboardConverter.convert_button(button)
                        for button in row
                    ]
                )
                for row in keyboard.inline_keyboard
            ]
        )
        return _keyboard

    @staticmethod
    def convert_reply_keyboard(
        keyboard: ReplyKeyboardMarkup,
    ) -> BottomKeyboard:
        _keyboard = BottomKeyboard(
            *[
                ButtonRow(
                    *[
                        KeyboardConverter.convert_button(button)
                        for button in row
                    ]
                )
                for row in keyboard.keyboard
            ]
        )
        return _keyboard
