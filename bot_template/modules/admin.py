from aiogram import types
from aiogram.filters.command import Command
from aiogram.filters.state import StateFilter

from bot_template import dp, utils
from bot_template.filters.is_admin import AdminFilter


@dp.message(Command("ram"), StateFilter("*"), AdminFilter())
async def ram_handler(message: types.Message):
    return await message.reply(f"RAM: {await utils.get_process_memory()}MB")


@dp.message(Command("uptime"), StateFilter("*"), AdminFilter())
async def uptime_handler(message: types.Message):
    return await message.reply(f"Uptime: {utils.get_uptime()}")
