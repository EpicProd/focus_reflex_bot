from typing import Union

from aiogram.filters import Filter
from aiogram.types import CallbackQuery, Message

from focus_reflex import admins


class AdminFilter(Filter):
    async def __call__(self, event: Union[Message, CallbackQuery]) -> bool:
        return event.from_user.id in admins  # type: ignore
