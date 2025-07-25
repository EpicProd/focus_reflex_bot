from typing import Any, Awaitable, Callable, Dict

import sentry_sdk
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sentry_sdk.integrations.aiohttp import AioHttpIntegration

from bot_template import config, dp


class SentryContextMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # TODO: my_chat_member
        if type(event).__name__ in [
            "Message",
            "CallbackQuery",
            "InlineQuery",
            "ChosenInlineResult",
        ]:
            sentry_sdk.set_user(
                {
                    "name": event.from_user.full_name,
                    "id": event.from_user.id,
                    "username": event.from_user.username,
                    "update": event.model_dump_json(),
                }
            )
        return await handler(event, data)


sentry_sdk.init(
    dsn=config.get_item("features.sentry", "public_key"),
    integrations=[AioHttpIntegration()],
    traces_sample_rate=config.get_item(
        "features.sentry", "traces_sample_rate"
    ),
)
dp.update.outer_middleware(SentryContextMiddleware())
