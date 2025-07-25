from aiogram import Bot, F, types
from aiogram.filters.command import Command
from aiogram.filters.state import StateFilter
from aiogram.fsm.context import FSMContext

from bot_template import dp
from bot_template.keyboards.models import (
    ButtonRow,
    InlineKeyboard,
    MarkdownViewWebAppButton,
    PayWebAppButton,
    SwitchInlineButton,
    URLButton,
    URLPayButton,
)
from bot_template.keyboards.models.base import ButtonRegistry
from bot_template.keyboards.models.inline_keyboard import CallbackButton
from bot_template.keyboards.models.multi_keyboard import WebAppButton
from bot_template.keyboards.utils.converter import KeyboardConverter


@dp.callback_query(F.data == "test_callback")
async def test_button(call: types.CallbackQuery, callback_data: dict):
    action = callback_data.get("action")
    match action:
        case "show_username":
            return await call.answer(
                f"SUCCESS!\n\nusername: @{callback_data['user'].username}",
                True,
            )
        case _:
            return await call.answer("SUCCESS!", True)


@dp.message(Command("reset_state"), StateFilter("*"))
async def start_handler(message: types.Message, state: FSMContext):
    if not await state.get_state():
        return await message.reply("no state active")
    await state.reset_state(with_data=False)
    return await message.reply("success")


@dp.message(Command("serialize"), StateFilter("*"))
async def serialize_handler(message: types.Message, state: FSMContext):
    if message.reply_to_message:
        keyboard = message.reply_to_message.reply_markup
        print(KeyboardConverter(keyboard))
        return await message.reply(
            "ok", reply_markup=KeyboardConverter(keyboard)
        )
    keyboard = InlineKeyboard(
        ButtonRow(CallbackButton("callback", "data", menu="menu")),
        ButtonRow(
            URLPayButton(300, "RUB", "https://google.com"),
            URLButton("google", "https://google.com"),
            SwitchInlineButton("switch", "switched"),
        ),
        ButtonRow(
            PayWebAppButton(300, "USD", "https://google.com"),
            MarkdownViewWebAppButton(
                "read",
                "https://raw.githubusercontent.com/rfoxxxy/telegram-bot-template/main/README.md",
            ),
        ),
    )
    print(ButtonRegistry.registry)
    print(keyboard.serialize())
    deserialized = InlineKeyboard.deserialize(keyboard.serialize())
    print(deserialized, deserialized._build().model_dump())
    await message.answer("not serialized", reply_markup=await keyboard.build())
    await message.answer(
        "serialized and deserialized", reply_markup=await deserialized.build()
    )


@dp.inline_query(F.query == "tests")
async def test_inline_handler(query: types.InlineQuery):
    keyboard = InlineKeyboard(
        ButtonRow(URLButton("google", "https://google.com"))
    )
    return await query.answer(
        [
            types.InlineQueryResultArticle(
                id=query.id + "1",
                title="test",
                reply_markup=await keyboard.build(),
                description="test object",
                input_message_content=types.InputTextMessageContent(
                    message_text="test"
                ),
            )
        ],
        cache_time=0,
    )


@dp.chosen_inline_result()
async def test_chosen_inline_handler(
    chosen: types.ChosenInlineResult, bot: Bot
):
    await bot.edit_message_text(
        f"test successful, {chosen.from_user.full_name}!",
        inline_message_id=chosen.inline_message_id,
    )
