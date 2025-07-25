from aiogram import F, flags, types
from aiogram.filters.command import Command, CommandObject

from bot_template import dp
from bot_template.database.models import User
from bot_template.keyboards.models import (
    ButtonRow,
    CallbackButton,
    InlineKeyboard,
    MarkdownViewWebAppButton,
    URLPayButton,
    WebAppButton,
)


@dp.message(Command("start"))
@flags.use_database
async def start_handler(message: types.Message, user: User):
    return await message.reply(
        f"hello, {user.name}! <b>some</b> <i>test</i>\n<u>moment</u>"
    )


@dp.message(Command("invoice"))
async def invoice_handler(message: types.Message):
    await message.answer_invoice(
        "test",
        "test text",
        "asdasd",
        "XTR",
        [types.LabeledPrice(label="test", amount=10)],
        "",
    )


@dp.pre_checkout_query()
async def pre_checkout(query: types.PreCheckoutQuery):
    return query.answer(True)


@dp.message(F.successful_payment)
async def paid_invoice_handler(message: types.Message):
    await message.answer(
        f"wow {message.successful_payment.telegram_payment_charge_id}"
    )


@dp.message(Command("refund"))
async def refund_handler(message: types.Message, command: CommandObject):
    payment_id = command.args
    await message.bot.refund_star_payment(message.from_user.id, payment_id)
    await message.answer("OK")


@dp.message(Command("test"))
@flags.use_database
async def test_handler(message: types.Message, user: User):
    keyboard = InlineKeyboard(
        ButtonRow(
            MarkdownViewWebAppButton(
                "Read me",
                "https://raw.githubusercontent.com/rfoxxxy/telegram-bot-template/main/README.md",
            )
        ),
        ButtonRow(
            CallbackButton(
                "test callback",
                "test_callback",
                action="show_username",
                user=user,
            ),
            WebAppButton(
                "test webapp", "https://hqd-slot-test.neonteam.cc/datamatrix"
            ),
            WebAppButton("open", "https://lossless-pay-test.neonteam.cc/pay"),
        ),
        ButtonRow(URLPayButton(10000, "USD", "https://google.com")),
    )
    return await message.reply("test!", reply_markup=await keyboard.build())
