from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message

from bot_template import cache, dp


class ThrottlingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[
            [CallbackQuery | Message, Dict[str, Any]], Awaitable[Any]
        ],
        event: CallbackQuery | Message,
        data: Dict[str, Any],
    ) -> Any:
        match type(event).__name__:
            case "Message":
                if (event.text or event.caption) and (event.text or event.caption).startswith("/"):  # type: ignore
                    if not cache.get(event.from_user.id):  # type: ignore
                        cache[event.from_user.id] = True  # type: ignore
                    else:
                        await event.reply(
                            "Тише-тише! Попробуй снова через 1 сек."
                        )
                        return
            case "CallbackQuery":
                if not cache.get(event.from_user.id):  # type: ignore
                    cache[event.from_user.id] = True  # type: ignore
                else:
                    await event.answer(
                        "Тише-тише! Попробуй снова через 1 сек.",
                        show_alert=True,
                    )
                    return
        return await handler(event, data)


dp.message.outer_middleware(ThrottlingMiddleware())
dp.callback_query.outer_middleware(ThrottlingMiddleware())
