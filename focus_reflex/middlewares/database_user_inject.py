import html
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import (
    CallbackQuery,
    ChosenInlineResult,
    InlineQuery,
    Message,
)

from focus_reflex import dp
from focus_reflex.database import database
from focus_reflex.database.exceptions import NotFoundError


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
            except NotFoundError:
                user = await database.register_user(event, data["session"])
            data["user"] = user
        return await handler(event, data)


dp.message.middleware(UserInjectorMiddleware())
dp.callback_query.middleware(UserInjectorMiddleware())
dp.inline_query.middleware(UserInjectorMiddleware())
dp.chosen_inline_result.middleware(UserInjectorMiddleware())
