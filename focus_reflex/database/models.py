from http import server
from sqlalchemy import ARRAY, BigInteger, Boolean, CheckConstraint, Column, String, Integer, DateTime, func, Text

from focus_reflex import db
from focus_reflex.database.extensions.mutable_list import MutableList
from focus_reflex.database.utils.mixins import BaseMixin


def default_days_send():
    return ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


class User(BaseMixin, db.Base):
    __tablename__ = "users"

    __table_args__ = (
        # order_mode: 0 = по порядку, 1 = случайно
        CheckConstraint("order_mode IN (0, 1)", name="valid_order_mode"),

        # per_day: 1..3
        CheckConstraint("per_day BETWEEN 1 AND 3", name="valid_per_day"),

        # time_mode: 0 = фикс., 1 = диапазон
        CheckConstraint("time_mode IN (0, 1)", name="valid_time_mode"),

        # time_fixed: 0..1435, шаг 5 минут
        CheckConstraint("time_fixed BETWEEN 0 AND 1435 AND time_fixed % 5 = 0", name="valid_time_fixed"),

        # range_start / range_end: 0..1435, start <= end
        CheckConstraint("range_start BETWEEN 0 AND 1435", name="valid_range_start"),
        CheckConstraint("range_end BETWEEN 0 AND 1435", name="valid_range_end"),
        CheckConstraint("range_start <= range_end", name="valid_range_bounds"),

        # days_mode: 0 = все, 1 = будни, 2 = выходные, 3 = кастом
        CheckConstraint("days_mode IN (0, 1, 2, 3)", name="valid_days_mode"),

        # days_send: если не пустой → только допустимые дни
        CheckConstraint(
            "days_send IS NULL OR cardinality(days_send) = 0 "
            "OR days_send <@ ARRAY['Mon','Tue','Wed','Thu','Fri','Sat','Sun']::text[]",
            name="valid_days_send"
        ),

        # questions: либо NULL, либо ≤ 20
        CheckConstraint(
            "questions IS NULL OR array_length(questions, 1) <= 20",
            name="max_20_questions"
        ),

        # next_q_idx: ≥ 0 и < 20
        CheckConstraint("next_q_idx >= 0 AND next_q_idx < 20", name="valid_next_q_idx"),
    )

    user_id = Column(BigInteger, primary_key=True, unique=True)
    send_in_pm = Column(Boolean, nullable=False, server_default="true")
    linked_channel_id = Column(BigInteger, nullable=True)
    questions = Column(MutableList.as_mutable(ARRAY(Text)), nullable=False, server_default='{}')
    next_q_idx = Column(Integer, nullable=False, server_default="0")
    order_mode = Column(Integer, nullable=False, server_default="1")
    per_day = Column(Integer, nullable=False, server_default="1")
    time_mode = Column(Integer, nullable=False, server_default="0")
    time_fixed = Column(Integer, nullable=False, server_default="540")
    range_start = Column(Integer, nullable=False, server_default="1140")
    range_end = Column(Integer, nullable=False, server_default="1200")
    next_send_local_ts = Column(DateTime(timezone=False), nullable=True)
    timezone = Column(String, nullable=False, server_default="Europe/Moscow")
    days_mode = Column(Integer, nullable=False, server_default="0")
    days_send = Column(MutableList.as_mutable(ARRAY(Text)), nullable=False, server_default='{Mon,Tue,Wed,Thu,Fri,Sat,Sun}')
    quiet = Column(Boolean, nullable=False, server_default="false")
    enabled = Column(Boolean, nullable=False, server_default="true")
    updated_at = Column(
        DateTime(timezone=False),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )


"""| Поле                          | Суть                                                                                                                |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| user_id                       | Telegram-ID владельца. Первичный ключ.                                                                               |
| send_in_pm                    | Куда слать. true → в личку, false — в канал.                                                                         |
| linked_channel_id             | ID канала.                                                                                                           |
| questions                     | Массив ≤ 20 текстов. Порядок сохранён.                                                                              |
| next_q_idx                    | Указатель для последовательной рассылки (1-based). при изменении вопросов надо как-то пересчитывать.                |
| order_mode                    | 0 — по порядку, 1 — случайно.                                                                                        |
| per_day                       | Сколько вопросов в сутки (1…3).                                                                                      |
| time_mode                     | 0 — одно точное время, 1 — диапазон.                                                                                 |
| time_fixed                    | Минуты от 00:00 (0…1435), шаг 5 мин; действует при time_mode = 0.                                                    |
| range_start / range_end       | Границы диапазона (в минутах от 00:00); при time_mode = 1.                                                           |
| next_send_local_ts            | Местное время (в минутах от 00:00), когда отправлять следующий вопрос.                                              |
| timezone                      | Текстовая таймзона пользователя (например, "Europe/Moscow").                                                         |
| days_mode                     | 0 — все дни, 1 — будни, 2 — выходные, 3 — кастом.                                                                    |
| days_send                     | Массив дней ["Mon", ..., "Sun] для варианта days_mode = 3.                                                           |
| quiet                         | TRUE → отправка без звука.                                                                                           |
| enabled                       | Рубильник: TRUE — рассылка активна.                                                                                  |
| updated_at                    | Время последнего изменения строки.                                                                                   |"""