from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import (
    CallbackQuery,
    ChosenInlineResult,
    InlineQuery,
    Message,
)

from bot_template import config, dp, logger
from bot_template.keyboards.utils import get_button_text


class LogMiddleware(BaseMiddleware):
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
        # print(event.model_dump_json())
        match type(event).__name__:
            case "Message":
                logger.info(
                    f"MESSAGE | user_id: {event.from_user.id} (name: {event.from_user.full_name} "  # type: ignore
                    f"| username: {event.from_user.username} | locale: {event.from_user.language_code}"  # type: ignore
                    f"{f' | chat: {event.chat.title} ({event.chat.username or event.chat.id})' if event.chat.id != event.from_user.id else ''}) | "  # type: ignore
                    f"text: {event.text or event.caption}"  # type: ignore
                )
            case "CallbackQuery":
                raw_data = data.get("callback_object", {}).get(
                    "query", event.data
                )
                button_text = get_button_text(event, raw_data)
                logger.info(
                    f"CALLBACK | user_id: {event.from_user.id} (name: {event.from_user.full_name} "  # type: ignore
                    f"| username: {event.from_user.username} | locale: {event.from_user.language_code}"  # type: ignore
                    f"{f' | chat: {event.message.chat.title} ({event.message.chat.username or event.message.chat.id})' if event.message.chat.id != event.from_user.id else ''}) | "  # type: ignore
                    f"{f'raw_data: {raw_data} | ' if config.get_item('features', 'use_modern_callback') else ''}"
                    f"data: {event.data} | button_text: {button_text}"  # type: ignore
                )
            case "InlineQuery":
                logger.info(
                    f"INLINE | user_id: {event.from_user.id} (name: {event.from_user.full_name}"  # type: ignore
                    f"| username: {event.from_user.username} | "  # type: ignore
                    f"locale: {event.from_user.language_code}) | data: {event.query}"  # type: ignore
                )
            case "ChosenInlineResult":
                logger.info(
                    f"CHOSEN INLINE | user_id: {event.from_user.id} (name: {event.from_user.full_name} | "  # type: ignore
                    f"username: {event.from_user.username} | locale: {event.from_user.language_code}) "  # type: ignore
                    f"| data: {event.query} | chosen: {event.result_id} (inline_message_id: {event.inline_message_id})"  # type: ignore
                )
        return await handler(event, data)


dp.message.outer_middleware(LogMiddleware())
dp.callback_query.outer_middleware(LogMiddleware())
dp.inline_query.outer_middleware(LogMiddleware())
dp.chosen_inline_result.outer_middleware(LogMiddleware())
