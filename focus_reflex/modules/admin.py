from aiogram import types, F
from aiogram.enums import ChatType
from aiogram.filters.command import Command
from aiogram.filters.state import StateFilter

from focus_reflex import dp, utils
from focus_reflex.filters.is_admin import AdminFilter


@dp.message(Command("ram"), StateFilter("*"), AdminFilter(), F.chat.type == ChatType.PRIVATE)
async def ram_handler(message: types.Message):
    return await message.reply(f"RAM: {await utils.get_process_memory()}MB")


@dp.message(Command("uptime"), StateFilter("*"), AdminFilter(), F.chat.type == ChatType.PRIVATE)
async def uptime_handler(message: types.Message):
    return await message.reply(f"Uptime: {utils.get_uptime()}")
