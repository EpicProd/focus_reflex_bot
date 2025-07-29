from loguru import logger

from apscheduler.triggers.cron import CronTrigger

from sqlalchemy import select

from focus_reflex import bots, db
from focus_reflex.core.task_manager.scheduler.base import BaseSchedulerTask
from focus_reflex.database import database
from focus_reflex.database.models import User
from focus_reflex.keyboards.models.inline_keyboard import CallbackButton, InlineKeyboard, ButtonRow
from focus_reflex.keyboards.models.multi_keyboard import WebAppButton


class CheckLinkedChannelsTask(BaseSchedulerTask):
    name = "check_linked_channels"
    trigger = CronTrigger(minute='0-59/10', second=5)  # каждые 10 минут + 5 секунд
    force_reschedule = True

    async def run_task(self, debug: bool = False, user_id: int | None = None):
        async with db.Session() as session:
            if False: # debug or not is_prod:
                users = [
                    await database.get_user(944176367, session),
                    await database.get_user(1404000244, session),
                ]
            elif user_id:
                users = [await database.get_user(user_id, session)]
            else:
                stmt = select(User).where(
                    User.tried_to_link_channel.is_(True),
                    User.linked_channel_id.is_(None)
                )
                result = await session.execute(stmt)
                users = result.scalars().all()

            logger.info(f"Checking {len(users)} users")

            for user in users:
                try:
                    keyboard = InlineKeyboard(ButtonRow(
                        WebAppButton("Открыть настройки", "https://focus-reflex.neonteam.cc")
                    ), ButtonRow(
                        CallbackButton("Закрыть", "close")
                    ))
                    await bots[0].send_message(user.user_id, "<b>⚠️Системное сообщение!</b>\n\n"
                                               "<blockquote>Бот зафиксировал попытку добавления на канал, но не получил информацию о канале\n\n"
                                               "Если вы добавили бота на канал, и в настройках до сих пор видите кнопку «привязать канал», то произошла ошибка\n\n"
                                               "Для надежности лучше удалить бота и добавить снова тем же способом.</blockquote>",
                                               reply_markup=await keyboard.build())
                except Exception as e:
                    logger.error(f"[{user.user_id}] Failed to send message: {e}")
                finally:
                    user.tried_to_link_channel = False
                    await session.commit()
            logger.info("Done")