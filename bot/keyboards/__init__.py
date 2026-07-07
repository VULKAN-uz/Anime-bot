"""
keyboards/__init__.py
"""
from bot.keyboards.inline import (
    get_anime_detail_keyboard,
    get_episodes_keyboard,
    get_anime_list_keyboard,
    get_subscription_keyboard,
    get_admin_panel_keyboard,
    get_back_to_admin_keyboard,
    get_favorites_keyboard,
    get_edit_anime_fields_keyboard,
    get_broadcast_confirm_keyboard,
    get_search_result_keyboard,
)
from bot.keyboards.reply import (
    get_main_keyboard,
    get_cancel_keyboard,
    get_skip_cancel_keyboard,
    get_confirmation_keyboard,
    get_admin_main_keyboard,
    get_more_episodes_keyboard,
    get_status_keyboard,
    remove_keyboard,
)

__all__ = [
    "get_anime_detail_keyboard",
    "get_episodes_keyboard",
    "get_anime_list_keyboard",
    "get_subscription_keyboard",
    "get_admin_panel_keyboard",
    "get_back_to_admin_keyboard",
    "get_favorites_keyboard",
    "get_edit_anime_fields_keyboard",
    "get_broadcast_confirm_keyboard",
    "get_search_result_keyboard",
    "get_main_keyboard",
    "get_cancel_keyboard",
    "get_skip_cancel_keyboard",
    "get_confirmation_keyboard",
    "get_admin_main_keyboard",
    "get_more_episodes_keyboard",
    "get_status_keyboard",
    "remove_keyboard",
]
