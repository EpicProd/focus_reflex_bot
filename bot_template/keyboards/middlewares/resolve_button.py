import pickle
from base64 import b64decode
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery

from bot_template.keyboards.database import database


class CallbackButtonMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: CallbackQuery,
        data: Dict[str, Any],
    ) -> Any:
        raw_callback_data = event.data
        resolved_data = await database.get_callback(raw_callback_data)
        if not resolved_data:
            data["callback_object"] = {}
            data["callback_data"] = {}
        elif resolved_data == "died":
            await event.answer(
                "Кнопка более неактивна. Повторите запрос.", True
            )
            return
        else:
            object.__setattr__(event, "data", resolved_data.original_query)
            # event.data = resolved_data.original_query
            data["callback_object"] = resolved_data.to_dict()
            data["callback_data"] = pickle.loads(
                b64decode(resolved_data.data.encode())
            )
        return await handler(event, data)
