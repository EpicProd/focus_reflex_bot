from datetime import datetime, timedelta
import pytz
from aiogram import F, flags, types
from aiogram.filters.command import Command
from aiogram.enums import ChatType

from focus_reflex import dp, db
from focus_reflex.database.models import User
from focus_reflex.keyboards.models import (
    ButtonRow,
    InlineKeyboard,
    WebAppButton,
)


@dp.message(Command("start"), F.chat.type == ChatType.PRIVATE)
@flags.use_database
async def start_handler(message: types.Message, user: User):
    keyboard = InlineKeyboard(ButtonRow(
        WebAppButton("Открыть настройки", "https://focus-reflex.neonteam.cc/")
    ))
    await message.bot.set_my_commands([
        types.BotCommand(command="start", description="Перезапуск бота"),
        types.BotCommand(command="stop", description="Остановить отправку вопросов"),
        types.BotCommand(command="reset", description="Сбросить настройки"),
        types.BotCommand(command="help", description="Справочная информация"),
    ])
    return await message.reply(
        "<b>Привет!</b>\n\n"
        "Этот бесплатный бот может присылать регулярно вопросы для рефлексии, чтобы помочь всем умным и осознанным организовать себе мини-Фокус.\n\n"
        "Ты сможешь выбрать, куда бот будет присылать вопросы: прямо сюда или в твой приватный тг-канал.\n\n"
        "<b>Команды:</b>\n"
        "/start – Перезапуск бота\n"
        "/stop – Остановить отправку вопросов\n"
        "/reset – Сбросить настройки\n"
        "/help – Справочная информация\n\n"
        "<b>Чтобы начать и настроить бота нажми на кнопку ниже.</b>",
        reply_markup=await keyboard.build()
    )

@dp.message(Command("help"), F.chat.type == ChatType.PRIVATE)
async def help_handler(message: types.Message):
    return await message.reply(
        "<b>Как начать получать вопросы?</b>\n"
        "Добавьте хотя бы вопросы на вкладке «Вопросы» и включите переключатель «Получать вопросы» вверху на вкладке настроек.\n\n"
        "<b>Куда будут приходить вопросы?</b>\n"
        "В чат с этим ботом.\n"
        "Но если у вас есть приватный тг-канал, который вы используете как дневник, то можно настроить, чтобы бот присылал вопросы туда. Для этого ему нужно дать права администратора и разрешить отправлять сообщения.\n\n"
        "<b>Когда будут приходить вопросы?</b>\n"
        "Выберите точное время или диапазон «от-до».\n"
        "В первом случае вопрос придет ровно в указанное время, а во втором — время будет выбрано случайно, но не раньше/позже указанных значений.\n\n"
        "<b>Нужно ли отвечать на вопросы через кнопку «Ответить» на канале или в боте?</b>\n"
        "Нет. Бот никак не фиксирует ваши ответы. Задача бота исключительно прислать вопрос.\n\n"
        "<b>Что делают остальные настройки:</b>\n"
        "<b>Порядок вопросов</b>: случайно или по порядку —  либо бот будет непредсказуемо присылать один вопрос из списка, либо в том порядке, как вы их загружали.\n"
        "<b>Часовой пояс</b>: бот будет присылать вопросы по этому часовому поясу.\n"
        "<b>Вопросов в день</b>: если вам мало 1 вопроса для рефлексии в день, то можно установить 2 или 3.\n"
        "<b>Тихий режим</b>: если включен, то сообщения от бота будут приходит без звука и уведомлений.\n"
        "<b>Дни недели</b>: можно выбрать выбрать дни, в которые вопросы будут приходить (если ячейка выделена белым, то день недели активен).\n\n"
        "<b>P.S.</b>\n"
        "Этот бот НЕ читает ваши личные каналы и не сохраняет ваши личные данные и/или сообщения. Вообще никакие и нигде. Вот исходный код бота, можете проверить, если разбираетесь: (когда-нибудь)",
    )

@dp.message(Command("stop"), F.chat.type == ChatType.PRIVATE)
@flags.use_database
async def stop_handler(message: types.Message, user: User, session: db.Session):
    user.enabled = False
    await session.commit()
    return await message.reply(
        "<b>Получать вопросы: выкл.</b>\n\n"
        "Чтобы включить – откройте меню настроек через кнопку в команде /start",
    )


@dp.message(Command("reset"), F.chat.type == ChatType.PRIVATE)
@flags.use_database
async def reset_handler(message: types.Message, user: User, session: db.Session):
    # Получаем текущее время в таймзоне пользователя
    tz = pytz.timezone(str(user.timezone))
    now_local = datetime.now(tz)
    
    # Добавляем 30 минут
    future_time = now_local + timedelta(minutes=30)
    
    # Получаем минуты от начала дня
    minutes_from_midnight = future_time.hour * 60 + future_time.minute
    
    # Округляем в большую сторону до кратного 5
    minutes_rounded = ((minutes_from_midnight + 4) // 5) * 5

    future_time_rounded = datetime.combine(future_time.date(), datetime.min.time()) + timedelta(minutes=minutes_rounded)
    
    # Учитываем переход через день (если больше 1439 минут)
    calculated_time_fixed = minutes_rounded % 1440
    
    user.next_send_local_ts = None
    user.days_mode = 0
    user.per_day = 1
    user.order_mode = 1
    user.time_mode = 0
    user.time_fixed = calculated_time_fixed
    user.range_start = 1140
    user.range_end = 1200
    user.days_send = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    user.quiet = False
    user.enabled = True
    await session.commit()
    keyboard = InlineKeyboard(ButtonRow(
        WebAppButton("Открыть настройки", "https://focus-reflex.neonteam.cc/")
    ))
    return await message.reply(
        "<b>Вы сбросили все настройки.</b>\n\n"
        f"Следующий случайный вопрос для рефлексии из вашего списка придет через 30 минут (в {future_time_rounded.strftime('%H:%M')})\n\n"
        "Чтобы изменить настройки – нажмите на кнопку ниже.",
        reply_markup=await keyboard.build()
    )