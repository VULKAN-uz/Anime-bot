"""
loader.py - Bot va Dispatcher yuklash
"""
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import BOT_TOKEN

# Bot instance
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)

# Storage (Redis ishlatish mumkin production da)
storage = MemoryStorage()

# Dispatcher
dp = Dispatcher(storage=storage)
