import asyncio
from typing import List

import babel.numbers
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    SwitchInlineQueryChosenChat,
)
from babel.core import Locale

try:
    from sqlalchemy.exc import OperationalError
except ImportError:
    pass

from bot_template import config
from bot_template.keyboards.database import database
from bot_template.keyboards.exceptions import UnsupportedTypeError
from bot_template.keyboards.models.base import BaseKeyboardButton, ButtonRow
from bot_template.keyboards.utils import KeyboardMarkupMixin, get_pay_text
from bot_template.utils import run_async


class CallbackButton(BaseKeyboardButton):
    """Inline keyboard button object"""

    def __init__(self, text: str, callback_data: str, **kwargs):
        super().__init__(
            "CallbackButton", text, callback_data, additional_data=kwargs
        )

    async def __encode_data(self, data: str, additional_data: dict) -> str:
        if config.get_item("features", "use_modern_callback"):
            try:
                callback = await database.add_callback(data, additional_data)
            except OperationalError:
                await database.init_database()
                return await self.__encode_data(data, additional_data)
            return callback.query  # type: ignore
        return data

    async def build_button(self, ctx):
        if type(ctx).__name__ == "BottomKeyboard":
            raise UnsupportedTypeError(
                f"Type {self.type} isn't supported in {type(ctx).__name__}"
            )
        return InlineKeyboardButton(
            text=self.text,
            callback_data=await self.__encode_data(
                self.callback_data, self.additional_data
            ),
        )

    @classmethod
    def deserialize(cls, data: dict):
        return cls(
            text=data["text"],
            callback_data=data["callback_data"],
            **data["additional_data"],
        )


class SwitchInlineButton(BaseKeyboardButton):
    """Inline keyboard button object"""

    def __init__(self, text: str, switch_inline_query: str):
        super().__init__(
            "SwitchInlineButton",
            text,
            switch_inline_query=switch_inline_query,
        )

    async def build_button(self, ctx):
        if type(ctx).__name__ == "BottomKeyboard":
            raise UnsupportedTypeError(
                f"Type {self.type} isn't supported in {type(ctx).__name__}"
            )
        return InlineKeyboardButton(
            text=self.text, switch_inline_query=self.switch_inline_query
        )

    @classmethod
    def deserialize(cls, data: dict):
        return cls(
            text=data["text"],
            switch_inline_query=data["switch_inline_query"],
        )

    @classmethod
    def deserialize(cls, data: dict):
        return cls(
            text=data["text"],
            switch_inline_query=data["switch_inline_query"],
        )


class SwitchInlineCurrentChatButton(BaseKeyboardButton):
    """Inline keyboard button object"""

    def __init__(self, text: str, switch_inline_query: str):
        super().__init__(
            "SwitchInlineCurrentChatButton",
            text,
            switch_inline_query=switch_inline_query,
        )

    async def build_button(self, ctx):
        if type(ctx).__name__ == "BottomKeyboard":
            raise UnsupportedTypeError(
                f"Type {self.type} isn't supported in {type(ctx).__name__}"
            )
        return InlineKeyboardButton(
            text=self.text,
            switch_inline_query_current_chat=self.switch_inline_query,
        )

    @classmethod
    def deserialize(cls, data: dict):
        return cls(
            text=data["text"],
            switch_inline_query=data["switch_inline_query"],
        )


class SwitchInlineChosenChatButton(BaseKeyboardButton):
    """Inline keyboard button object"""

    def __init__(
        self,
        text: str,
        switch_inline_query: str,
        allow_user_chats: bool = True,
        allow_bot_chats: bool = True,
        allow_group_chats: bool = True,
        allow_channel_chats: bool = True,
    ):
        self.allow_user_chats = allow_user_chats
        self.allow_bot_chats = allow_bot_chats
        self.allow_group_chats = allow_group_chats
        self.allow_channel_chats = allow_channel_chats
        super().__init__(
            "SwitchInlineChosenChatButton",
            text,
            switch_inline_query=switch_inline_query,
        )

    async def build_button(self, ctx):
        if type(ctx).__name__ == "BottomKeyboard":
            raise UnsupportedTypeError(
                f"Type {self.type} isn't supported in {type(ctx).__name__}"
            )
        return InlineKeyboardButton(
            text=self.text,
            switch_inline_query_chosen_chat=SwitchInlineQueryChosenChat(
                query=self.switch_inline_query,
                allow_user_chats=self.allow_user_chats,
                allow_bot_chats=self.allow_bot_chats,
                allow_group_chats=self.allow_group_chats,
                allow_channel_chats=self.allow_channel_chats,
            ),
        )

    def serialize(self) -> dict:
        return {
            "type": self.type,
            "text": self.text,
            "switch_inline_query": self.switch_inline_query,
            "allow_user_chats": self.allow_user_chats,
            "allow_bot_chats": self.allow_bot_chats,
            "allow_group_chats": self.allow_group_chats,
            "allow_channel_chats": self.allow_channel_chats,
        }

    @classmethod
    def deserialize(cls, data: dict):
        return cls(
            text=data["text"],
            switch_inline_query=data["switch_inline_query"],
            allow_user_chats=data["allow_user_chats"],
            allow_bot_chats=data["allow_bot_chats"],
            allow_group_chats=data["allow_group_chats"],
            allow_channel_chats=data["allow_channel_chats"],
        )


class UserProfileButton(BaseKeyboardButton):
    """Inline keyboard button object"""

    def __init__(self, text: str, user_id: int):
        super().__init__(
            "UserProfileButton", text, url=f"tg://user?id={user_id}"
        )

    async def build_button(self, ctx):
        if type(ctx).__name__ == "BottomKeyboard":
            raise UnsupportedTypeError(
                f"Type {self.type} isn't supported in {type(ctx).__name__}"
            )
        return InlineKeyboardButton(text=self.text, url=self.url)

    def serialize(self) -> dict:
        return {"type": self.type, "text": self.text, "user_id": self.user_id}

    @classmethod
    def deserialize(cls, data: dict):
        return cls(text=data["text"], user_id=data["user_id"])

    def serialize(self) -> dict:
        return {
            "type": self.type,
            "price": self.price,
            "val": self.val,
            "locale": self.locale,
        }

    @classmethod
    def deserialize(cls, data: dict):
        return cls(price=data["price"], val=data["val"], locale=data["locale"])


class PayButton(BaseKeyboardButton):
    """Inline keyboard button object"""

    def __init__(self, price: float, val: str, locale: str | Locale = None):
        self.price = price
        self.val = val
        self.locale = locale
        if not self.locale:
            self.locale = "en"
        super().__init__(
            "PayButton",
            f"{get_pay_text(str(locale))} {babel.numbers.format_currency(self.price, self.val, locale=self.locale)}",
        )

    async def build_button(self, ctx):
        if type(ctx).__name__ == "BottomKeyboard":
            raise UnsupportedTypeError(
                f"Type {self.type} isn't supported in {type(ctx).__name__}"
            )
        return InlineKeyboardButton(text=self.text, pay=True)

    def serialize(self) -> dict:
        return {
            "type": self.type,
            "price": self.price,
            "val": self.val,
            "locale": self.locale,
        }

    @classmethod
    def deserialize(cls, data: dict):
        return cls(price=data["price"], val=data["val"], locale=data["locale"])


class URLButton(BaseKeyboardButton):
    """Bottom keyboard button object"""

    def __init__(self, text: str, url: str):
        super().__init__("URLButton", text, url=url)

    async def build_button(self, ctx):
        if type(ctx).__name__ == "BottomKeyboard":
            raise UnsupportedTypeError(
                f"Type {self.type} isn't supported in {type(ctx).__name__}"
            )
        return InlineKeyboardButton(text=self.text, url=self.url)

    @classmethod
    def deserialize(cls, data: dict):
        return cls(
            text=data["text"],
            url=data["url"],
        )

    @classmethod
    def deserialize(cls, data: dict):
        return cls(
            text=data["text"],
            url=data["url"],
        )


class URLPayButton(BaseKeyboardButton):
    """Bottom keyboard button object"""

    def __init__(
        self, price: float, val: str, url: str, locale: str | Locale = None
    ):
        self.price = price
        self.val = val
        self.locale = locale
        if not self.locale:
            self.locale = "en"
        super().__init__(
            "URLPayButton",
            f"{get_pay_text(str(locale))} {babel.numbers.format_currency(self.price, self.val, locale=self.locale)}",
            url=url,
        )

    async def build_button(self, ctx):
        if type(ctx).__name__ == "BottomKeyboard":
            raise UnsupportedTypeError(
                f"Type {self.type} isn't supported in {type(ctx).__name__}"
            )
        return InlineKeyboardButton(text=self.text, url=self.url)

    def serialize(self) -> dict:
        return {
            "type": self.type,
            "url": self.url,
            "price": self.price,
            "val": self.val,
            "locale": self.locale,
        }

    @classmethod
    def deserialize(cls, data: dict):
        return cls(
            url=data["url"],
            price=data["price"],
            val=data["val"],
            locale=data["locale"],
        )

    def serialize(self) -> dict:
        return {
            "type": self.type,
            "url": self.url,
            "price": self.price,
            "val": self.val,
            "locale": self.locale,
        }

    @classmethod
    def deserialize(cls, data: dict):
        return cls(
            url=data["url"],
            price=data["price"],
            val=data["val"],
            locale=data["locale"],
        )


class InlineKeyboard(KeyboardMarkupMixin):
    __slots__ = ["rows"]

    def __init__(self, *args: ButtonRow) -> None:
        self.rows: List[ButtonRow] = list(args) if args else []

    async def build(self) -> "InlineKeyboardMarkup":
        """Build keyboard markup

        Raises:
            UnsupportedTypeError: if specified unsupported button type

        Returns:
            InlineKeyboardMarkup: aiogram keyboard markup object
        """
        rows = [
            asyncio.gather(*[btn.build_button(self) for btn in row.buttons])
            for row in self.rows
        ]

        buttons_in_rows = await asyncio.gather(*rows)

        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons_in_rows)

        return keyboard

    def _build(self) -> InlineKeyboardMarkup:
        """
        Synchronously builds keyboard markup
        """
        return run_async(self.build)
