"""handlers/__init__.py"""
from bot.handlers.user import router as user_router
from bot.handlers.admin import router as admin_router
from bot.handlers.search import router as search_router
from bot.handlers.callback import router as callback_router

__all__ = ["user_router", "admin_router", "search_router", "callback_router"]
