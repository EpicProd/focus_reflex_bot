import html
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import (
    CallbackQuery,
    ChosenInlineResult,
    InlineQuery,
    Message,
)

from bot_template import dp
from bot_template.database import database
from bot_template.database.exceptions import NotFoundError


class UserInjectorMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[
            [
                CallbackQuery | ChosenInlineResult | InlineQuery | Message,
                Dict[str, Any],
            ],
            Awaitable[Any],
        ],
        event: CallbackQuery | ChosenInlineResult | InlineQuery | Message,
        data: Dict[str, Any],
    ) -> Any:
        if "session" in data:
            try:
                user = await database.get_user(
                    event.from_user.id, data["session"]  # type: ignore
                )
                if user.username != event.from_user.username:  # type: ignore
                    user.username = event.from_user.username  # type: ignore
                if user.name != html.escape(event.from_user.full_name):  # type: ignore
                    user.name = html.escape(event.from_user.full_name)  # type: ignore
                await data["session"].commit()
            except NotFoundError:
                user = await database.register_user(event, data["session"])
            data["user"] = user
        return await handler(event, data)


dp.message.middleware(UserInjectorMiddleware())
dp.callback_query.middleware(UserInjectorMiddleware())
dp.inline_query.middleware(UserInjectorMiddleware())
dp.chosen_inline_result.middleware(UserInjectorMiddleware())
