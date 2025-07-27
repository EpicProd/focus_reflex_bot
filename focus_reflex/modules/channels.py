from aiogram import types
from aiogram.enums import ChatMemberStatus, ChatType
from sqlalchemy import select

from focus_reflex import db, dp
from focus_reflex.database import database
from focus_reflex.keyboards.models.base import ButtonRow
from focus_reflex.keyboards.models.inline_keyboard import InlineKeyboard
from focus_reflex.keyboards.models.multi_keyboard import WebAppButton


@dp.my_chat_member()
async def bot_added_to_channel_handler(my_chat_member: types.ChatMemberUpdated):
    """Обработчик добавления/удаления бота в канал"""
    async with db.Session() as session:
        # Проверяем, что это канал
        if my_chat_member.chat.type != ChatType.CHANNEL:
            return
        channel_id = my_chat_member.chat.id
        user_id = my_chat_member.from_user.id
        
        # Обработка удаления/исключения бота из канала
        if my_chat_member.new_chat_member.status in [ChatMemberStatus.LEFT, ChatMemberStatus.KICKED]:
            try:
                # Ищем пользователя, у которого привязан этот канал
                result = await session.execute(
                    select(database.User).where(database.User.linked_channel_id == channel_id)
                )
                user = result.scalar_one_or_none()
                
                if user is None:
                    return
                
                user.linked_channel_id = None
                await session.commit()
                
                # Отправляем уведомление об отвязке
                try:
                    keyboard = InlineKeyboard(ButtonRow(
                        WebAppButton("Открыть настройки", "https://focus-reflex.neonteam.cc/")
                    ))
                    await my_chat_member.bot.send_message(
                        chat_id=user.user_id,
                        text=f"❌ Канал <b>{my_chat_member.chat.title}</b> был отвязан от вашего аккаунта.\n\n"
                             f"Вопросы больше не будут отправляться в этот канал.",
                        reply_markup=await keyboard.build()
                    )
                except Exception as e:
                    print(f"Failed to send notification to user {user.user_id}: {e}")
            except Exception as e:
                print(f"Failed to process channel unlink: {e}")
            return
        
        # Обработка добавления бота в канал
        if my_chat_member.new_chat_member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER]:
            return
        
        # Проверяем, что это именно добавление (а не изменение прав)
        if (my_chat_member.old_chat_member.status != ChatMemberStatus.LEFT and 
            my_chat_member.old_chat_member.status != ChatMemberStatus.KICKED):
            return
        
        channel_id = my_chat_member.chat.id
        user_id = my_chat_member.from_user.id
        
        try:
            # Получаем информацию о пользователе в канале
            channel_member = await my_chat_member.chat.get_member(user_id)
            
            # Проверяем, что пользователь является владельцем канала
            if channel_member.status != ChatMemberStatus.CREATOR:
                return
            
            # Получаем или создаем пользователя в базе данных
            try:
                user = await database.get_user(user_id, session)
            except Exception:
                return
            
            # Обновляем linked_channel_id
            user.linked_channel_id = channel_id
            await session.commit()
            
            # Отправляем уведомление в ЛС пользователю
            try:
                keyboard = InlineKeyboard(ButtonRow(
                    WebAppButton("Открыть настройки", "https://focus-reflex.neonteam.cc/")
                ))
                await my_chat_member.bot.send_message(
                    chat_id=user_id,
                    text=f"✅ Канал <b>{my_chat_member.chat.title}</b> успешно привязан к вашему аккаунту!\n\n"
                        f"Теперь вопросы будут отправляться в этот канал.\n\n"
                        f"Чтобы отвязать канал, удалите бота из него.",
                    reply_markup=await keyboard.build()
                )
            except Exception as e:
                # Если не удается отправить сообщение в ЛС (например, пользователь заблокировал бота)
                # Логируем ошибку, но не падаем
                print(f"Failed to send notification to user {user_id}: {e}")
                
        except Exception as e:
            print(f"Error processing bot addition to channel: {e}")
