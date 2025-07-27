import datetime
import random
import pytz
from asyncio import sleep

from aiogram import exceptions
from loguru import logger

from apscheduler.triggers.cron import CronTrigger

from sqlalchemy import select, func

from focus_reflex import bots, db, is_prod
from focus_reflex.core.task_manager.scheduler.base import BaseSchedulerTask
from focus_reflex.database import database
from focus_reflex.database.models import User


WEEKDAY_STR = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


class SendQuestionsTask(BaseSchedulerTask):
    name = "send_questions"
    trigger = CronTrigger(minute='0-59/5', second=5)  # каждые 5 минут + 5 секунд
    force_reschedule = True

    async def run_task(self, debug: bool = False, user_id: int | None = None):
        now_utc = datetime.datetime.now(datetime.UTC)

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
                    User.enabled.is_(True),
                    User.questions.isnot(None),
                    func.array_length(User.questions, 1) > 0
                )
                result = await session.execute(stmt)
                users = result.scalars().all()

            logger.info(f"Checking {len(users)} users at {now_utc.isoformat()} UTC")

            for user in users:
                try:
                    tz = pytz.timezone(user.timezone)
                    now_local = now_utc.astimezone(tz)
                    today_str = WEEKDAY_STR[now_local.weekday()]
                except Exception:
                    logger.warning(f"[{user.user_id}] Invalid timezone: {user.timezone}, skipping")
                    continue

                if not user.next_send_local_ts:
                    # Инициализируем время отправки: сегодня если возможно, иначе завтра
                    if _is_day_allowed(user, today_str):
                        # Сегодня разрешенный день, проверяем время
                        today_base = datetime.datetime.combine(now_local.date(), datetime.time(0, 0))
                        today_base = tz.localize(today_base)
                        
                        if user.time_mode == 0:
                            # Фиксированное время
                            target_time = today_base + datetime.timedelta(minutes=user.time_fixed)
                        else:
                            # Диапазон времени - планируем в оставшейся части дня
                            current_minutes = now_local.hour * 60 + now_local.minute
                            current_minutes_rounded = (current_minutes // 5) * 5  # Округляем до 5 минут
                            
                            # Определяем эффективный диапазон для планирования
                            effective_start = max(user.range_start, current_minutes_rounded + 5)  # +5 минут от текущего времени
                            effective_end = user.range_end
                            
                            if effective_start <= effective_end:
                                # Есть оставшееся время в диапазоне сегодня
                                rand_minute = random.randint(effective_start // 5, effective_end // 5) * 5
                                target_time = today_base + datetime.timedelta(minutes=rand_minute)
                                logger.info(f"[{user.user_id}] Planned in remaining range: {effective_start}-{effective_end} min, selected {rand_minute}")
                            else:
                                # Диапазон уже закончился, планируем на завтра
                                next_time = _get_next_valid_send_time(user, now_local, tz)
                                user.next_send_local_ts = next_time.replace(tzinfo=None)
                                logger.info(f"[{user.user_id}] Range ended, planned for tomorrow: {next_time}")
                                continue
                        
                        # Сравниваем время без секунд
                        target_time_no_seconds = target_time.replace(second=0, microsecond=0)
                        now_local_no_seconds = now_local.replace(second=0, microsecond=0)
                        
                        if target_time_no_seconds > now_local_no_seconds:
                            # Время еще не прошло, ставим на сегодня
                            user.next_send_local_ts = target_time.replace(tzinfo=None)
                            logger.info(f"[{user.user_id}] Initialized next_send_local_ts for today: {target_time}")
                            continue
                        elif target_time_no_seconds == now_local_no_seconds:
                            # Время точно совпадает, отправляем сразу и планируем на завтра
                            logger.info(f"[{user.user_id}] Time matches exactly, sending now and planning for tomorrow")
                            # Устанавливаем next_send_local_ts как будто уже было запланировано
                            user.next_send_local_ts = target_time.replace(tzinfo=None)
                            # НЕ делаем continue - продолжаем выполнение для отправки
                        else:
                            # Время уже прошло, ставим на завтра
                            next_time = _get_next_valid_send_time(user, now_local, tz)
                            user.next_send_local_ts = next_time.replace(tzinfo=None)
                            logger.info(f"[{user.user_id}] Initialized next_send_local_ts for tomorrow: {next_time}")
                            continue
                    else:
                        # Сегодня запрещенный день, ставим на следующий валидный
                        next_time = _get_next_valid_send_time(user, now_local, tz)
                        user.next_send_local_ts = next_time.replace(tzinfo=None)
                        logger.info(f"[{user.user_id}] Initialized next_send_local_ts for next valid day: {next_time}")
                        continue

                # Сравниваем naive времена (убираем timezone из текущего времени)
                if user.next_send_local_ts > now_local.replace(tzinfo=None):
                    logger.debug(f"[{user.user_id}] Skipped: too early ({user.next_send_local_ts} > {now_local.replace(tzinfo=None)})")
                    continue

                if not _is_day_allowed(user, today_str):
                    logger.info(f"[{user.user_id}] Skipped: day '{today_str}' not allowed")
                    next_time = _get_next_valid_send_time(user, now_local, tz)
                    user.next_send_local_ts = next_time.replace(tzinfo=None)
                    continue

                if not user.questions:
                    logger.info(f"[{user.user_id}] Skipped: no questions")
                    continue

                # Выбор вопросов (per_day штук)
                questions_to_send = []
                if user.order_mode == 0:
                    # Последовательный режим
                    current_idx = user.next_q_idx
                    
                    # Определяем сколько вопросов отправлять: не больше чем есть в наличии
                    questions_to_send_count = min(user.per_day, len(user.questions))
                    
                    for i in range(questions_to_send_count):
                        if current_idx >= len(user.questions):
                            current_idx = 0
                        questions_to_send.append(user.questions[current_idx])
                        current_idx += 1
                    
                    user.next_q_idx = current_idx
                    if user.next_q_idx >= len(user.questions):
                        user.next_q_idx = 0
                    logger.debug(f"[{user.user_id}] Selected {len(questions_to_send)} questions (sequential, starting from {user.next_q_idx - len(questions_to_send) + 1})")
                else:
                    # Случайный режим
                    if user.per_day >= len(user.questions):
                        questions_to_send = list(user.questions)
                        random.shuffle(questions_to_send)
                    else:
                        questions_to_send = random.sample(user.questions, user.per_day)
                    logger.debug(f"[{user.user_id}] Selected {len(questions_to_send)} questions (random)")

                # Отправка
                try:
                    # Определяем куда отправлять
                    if user.send_in_pm or not user.linked_channel_id:
                        chat_id = int(user.user_id)
                    else:
                        chat_id = int(user.linked_channel_id)

                    # Отправляем каждый вопрос отдельным сообщением
                    for question in questions_to_send:
                        await bots[0].send_message(
                            chat_id=chat_id,
                            text=str(question),
                            disable_notification=bool(user.quiet)
                        )
                    
                    logger.info(f"[{user.user_id}] Sent {len(questions_to_send)} questions successfully")
                except exceptions.TelegramAPIError as e:
                    logger.error(f"[{user.user_id}] Send failed: {e}")
                    continue

                # Планирование следующей отправки
                next_time = _get_next_valid_send_time(user, now_local, tz)
                user.next_send_local_ts = next_time.replace(tzinfo=None)
                logger.debug(f"[{user.user_id}] Next send planned at {next_time}")

            await session.commit()


def _is_day_allowed(user: User, day: str) -> bool:
    if user.days_mode == 0:
        return True
    elif user.days_mode == 1:
        return day in ["Mon", "Tue", "Wed", "Thu", "Fri"]
    elif user.days_mode == 2:
        return day in ["Sat", "Sun"]
    elif user.days_mode == 3:
        return day in user.days_send
    return False


def _get_next_valid_send_time(user: User, after: datetime.datetime, tz) -> datetime.datetime:
    """
    Возвращает локальное время следующей допустимой отправки (с минутами, кратными 5)
    """
    candidate = after
    for _ in range(14):  # максимум 2 недели вперёд
        candidate += datetime.timedelta(days=1)
        day_str = WEEKDAY_STR[candidate.weekday()]
        if _is_day_allowed(user, day_str):
            base = datetime.datetime.combine(candidate.date(), datetime.time(0, 0))
            base = tz.localize(base)

            if user.time_mode == 0:
                minute = (user.time_fixed // 5) * 5
                return base + datetime.timedelta(minutes=minute)
            else:
                rand_minute = random.randint(user.range_start // 5, user.range_end // 5) * 5
                return base + datetime.timedelta(minutes=rand_minute)

    # fallback через 1 день в 00:00 + фикс
    base = tz.localize(datetime.datetime.combine(
        (after + datetime.timedelta(days=1)).date(),
        datetime.time(0, 0)
    ))
    return base + datetime.timedelta(minutes=user.time_fixed)
