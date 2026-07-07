"""
handlers/callback.py - Umumiy callback handlerlari
"""
from aiogram import F, Router
from aiogram.types import CallbackQuery

router = Router(name="callback")


@router.callback_query(F.data == "noop")
async def noop(callback: CallbackQuery) -> None:
    await callback.answer()


@router.callback_query(F.data == "close")
async def close_message(callback: CallbackQuery) -> None:
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.answer()
