from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.dispatcher.flags import get_flag
from aiogram.types import (
    CallbackQuery,
    ChosenInlineResult,
    InlineQuery,
    Message,
)
from loguru import logger

from bot_template import db, dp


class DatabaseInjectorMiddleware(BaseMiddleware):
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
        if get_flag(data, "use_database"):
            async with db.Session() as session:
                data["session"] = session
                await handler(event, data)
                logger.debug(data)
        else:
            return await handler(event, data)


dp.message.middleware(DatabaseInjectorMiddleware())
dp.callback_query.middleware(DatabaseInjectorMiddleware())
dp.inline_query.middleware(DatabaseInjectorMiddleware())
dp.chosen_inline_result.middleware(DatabaseInjectorMiddleware())
