from typing import Union

from aiogram.enums import ChatMemberStatus
from aiogram.filters import Filter
from aiogram.types import CallbackQuery, Message


class ChatAdminFilter(Filter):
    async def __call__(self, event: Union[Message, CallbackQuery]) -> bool:
        msg = event.message if isinstance(event, CallbackQuery) else event
        if msg.chat.id == msg.from_user.id:  # type: ignore
            return True
        member = await msg.chat.get_member(event.from_user.id)  # type: ignore
        if isinstance(event, Message) and member.status not in [
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.CREATOR,
        ]:
            return False
        return member.status in [
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.CREATOR,
        ]
