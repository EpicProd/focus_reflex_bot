import asyncio
from typing import List

from aiogram.types import (
    KeyboardButton,
    KeyboardButtonPollType,
    ReplyKeyboardMarkup,
)

from bot_template.keyboards.exceptions import UnsupportedTypeError
from bot_template.keyboards.models.base import BaseKeyboardButton, ButtonRow
from bot_template.keyboards.utils import KeyboardMarkupMixin
from bot_template.utils import run_async


class TextButton(BaseKeyboardButton):
    """Bottom keyboard button object"""

    def __init__(self, text: str):
        super().__init__("TextButton", text)

    async def build_button(self, ctx):
        if type(ctx).__name__ == "InlineKeyboard":
            raise UnsupportedTypeError(
                f"Type {self.type} isn't supported in {type(ctx).__name__}"
            )
        return KeyboardButton(text=self.text)

    @classmethod
    def deserialize(cls, data: dict):
        return cls(text=data["text"])

    @classmethod
    def deserialize(cls, data: dict):
        return cls(text=data["text"])


class RequestContactButton(BaseKeyboardButton):
    """Bottom keyboard button object"""

    def __init__(self, text: str):
        super().__init__("RequestContactButton", text)

    async def build_button(self, ctx):
        if type(ctx).__name__ == "InlineKeyboard":
            raise UnsupportedTypeError(
                f"Type {self.type} isn't supported in {type(ctx).__name__}"
            )
        return KeyboardButton(text=self.text, request_contact=True)

    @classmethod
    def deserialize(cls, data: dict):
        return cls(text=data["text"])

    @classmethod
    def deserialize(cls, data: dict):
        return cls(text=data["text"])


class RequestLocationButton(BaseKeyboardButton):
    """Bottom keyboard button object"""

    def __init__(self, text: str):
        super().__init__("RequestLocationButton", text)

    async def build_button(self, ctx):
        if type(ctx).__name__ == "InlineKeyboard":
            raise UnsupportedTypeError(
                f"Type {self.type} isn't supported in {type(ctx).__name__}"
            )
        return KeyboardButton(text=self.text, request_location=True)

    @classmethod
    def deserialize(cls, data: dict):
        return cls(text=data["text"])

    @classmethod
    def deserialize(cls, data: dict):
        return cls(text=data["text"])


class RequestPollButton(BaseKeyboardButton):
    """Bottom keyboard button object"""

    def __init__(self, text: str, poll_type: str):
        super().__init__("RequestPollButton", text, poll_type=poll_type)

    async def build_button(self, ctx):
        if type(ctx).__name__ == "InlineKeyboard":
            raise UnsupportedTypeError(
                f"Type {self.type} isn't supported in {type(ctx).__name__}"
            )
        return KeyboardButton(
            text=self.text,
            request_poll=KeyboardButtonPollType(type=self.poll_type),
        )

    @classmethod
    def deserialize(cls, data: dict):
        return cls(text=data["text"], poll_type=data["poll_type"])


class BottomKeyboard(KeyboardMarkupMixin):
    __slots__ = ["rows"]

    def __init__(self, *args: ButtonRow) -> None:
        self.rows: List[ButtonRow] = list(args) if args else []

    async def build(
        self,
        resize: bool = True,
        one_time: bool = False,
        placeholder: str = None,
        selective: bool = False,
    ) -> "ReplyKeyboardMarkup":
        """Build keyboard markup

        Raises:
            UnsupportedTypeError: if specified unsupported button type

        Returns:
            ReplyKeyboardMarkup: aiogram keyboard markup object
        """
        rows = [
            asyncio.gather(*[btn.build_button(self) for btn in row.buttons])
            for row in self.rows
        ]

        buttons_in_rows = await asyncio.gather(*rows)

        keyboard = ReplyKeyboardMarkup(
            keyboard=buttons_in_rows,
            resize_keyboard=resize,
            one_time_keyboard=one_time,
            input_field_placeholder=placeholder,
            selective=selective,
        )
        return keyboard

    def _build(self) -> ReplyKeyboardMarkup:
        """
        Synchronously builds keyboard markup
        """
        return run_async(self.build)
