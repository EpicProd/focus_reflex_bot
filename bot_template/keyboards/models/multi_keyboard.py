import html

import babel.numbers
import validators
from aiogram.types import InlineKeyboardButton, KeyboardButton, WebAppInfo
from babel import Locale

from bot_template.keyboards.exceptions import UnsupportedTypeError
from bot_template.keyboards.models.base import BaseKeyboardButton
from bot_template.keyboards.utils import get_pay_text


class WebAppButton(BaseKeyboardButton):
    """Bottom and inline keyboard button object"""

    def __init__(self, text: str, webapp_url: str):
        super().__init__("WebAppButton", text, url=webapp_url)

    async def build_button(self, ctx):
        match type(ctx).__name__:
            case "InlineKeyboard":
                return InlineKeyboardButton(
                    text=self.text, web_app=WebAppInfo(url=self.url)
                )
            case "BottomKeyboard":
                return KeyboardButton(
                    text=self.text, web_app=WebAppInfo(url=self.url)
                )
            case _:
                raise UnsupportedTypeError(
                    f"Type {self.type} isn't supported in {type(ctx).__name__}"
                )

    @classmethod
    def deserialize(cls, data: dict):
        return cls(
            text=data["text"],
            webapp_url=data["webapp_url"],
        )


class PayWebAppButton(BaseKeyboardButton):
    """Bottom and inline keyboard button object"""

    def __init__(
        self,
        price: float,
        val: str,
        webapp_url: str,
        locale: str | Locale = None,
    ):
        self.price = price
        self.val = val
        self.locale = locale
        if not self.locale:
            self.locale = "en"
        super().__init__(
            "PayWebAppButton",
            f"{get_pay_text(str(locale))} {babel.numbers.format_currency(self.price, self.val, locale=self.locale)}",
            url=webapp_url,
        )

    async def build_button(self, ctx):
        match type(ctx).__name__:
            case "InlineKeyboard":
                return InlineKeyboardButton(
                    text=self.text, web_app=WebAppInfo(url=self.url)
                )
            case "BottomKeyboard":
                return KeyboardButton(
                    text=self.text, web_app=WebAppInfo(url=self.url)
                )
            case _:
                raise UnsupportedTypeError(
                    f"Type {self.type} isn't supported in {type(ctx).__name__}"
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
            webapp_url=data["url"],
            price=data["price"],
            val=data["val"],
            locale=data["locale"],
        )


class MarkdownViewWebAppButton(BaseKeyboardButton):
    """Bottom and inline keyboard button object"""

    def __init__(self, text: str, md_url: str):
        self.md_url = md_url
        _md_url = (
            f"https://static.neonteam.cc/{self.md_url}"
            if not validators.url(self.md_url, public=True)
            else self.md_url
        )
        super().__init__(
            "MarkdownViewWebAppButton",
            text,
            url=f"https://static.neonteam.cc/tgmd.html?url={html.escape(_md_url)}",
        )

    async def build_button(self, ctx):
        match type(ctx).__name__:
            case "InlineKeyboard":
                return InlineKeyboardButton(
                    text=self.text, web_app=WebAppInfo(url=self.url)
                )
            case "BottomKeyboard":
                return KeyboardButton(
                    text=self.text, web_app=WebAppInfo(url=self.url)
                )
            case _:
                raise UnsupportedTypeError(
                    f"Type {self.type} isn't supported in {type(ctx).__name__}"
                )

    def serialize(self) -> dict:
        return {
            "type": self.type,
            "text": self.text,
            "url": self.md_url,
        }

    @classmethod
    def deserialize(cls, data: dict):
        return cls(
            text=data["text"],
            md_url=data["url"],
        )
