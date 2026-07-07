"""
states/__init__.py - FSM Holatlar
===================================
Barcha FSM holatlari shu yerda.
"""

from aiogram.fsm.state import State, StatesGroup


class SearchState(StatesGroup):
    """Qidiruv holatlari"""
    waiting_for_code = State()
    waiting_for_image = State()
    waiting_for_name = State()


class AddAnimeState(StatesGroup):
    """Anime qo'shish holatlari"""
    waiting_for_code = State()
    waiting_for_name = State()
    waiting_for_poster = State()
    waiting_for_description = State()
    waiting_for_genre = State()
    waiting_for_year = State()
    waiting_for_duration = State()
    waiting_for_language = State()
    waiting_for_rating = State()
    waiting_for_episodes_count = State()
    waiting_for_status = State()
    waiting_for_confirmation = State()


class AddEpisodeState(StatesGroup):
    """Qism qo'shish holatlari"""
    waiting_for_anime_code = State()
    waiting_for_episode_number = State()
    waiting_for_video = State()
    waiting_for_more = State()


class EditAnimeState(StatesGroup):
    """Anime tahrirlash holatlari"""
    waiting_for_anime_code = State()
    waiting_for_field = State()
    waiting_for_value = State()


class DeleteAnimeState(StatesGroup):
    """Anime o'chirish holatlari"""
    waiting_for_anime_code = State()
    waiting_for_confirmation = State()


class DeleteEpisodeState(StatesGroup):
    """Qism o'chirish holatlari"""
    waiting_for_anime_code = State()
    waiting_for_episode_number = State()
    waiting_for_confirmation = State()


class ChangePosterState(StatesGroup):
    """Poster almashtirish holatlari"""
    waiting_for_anime_code = State()
    waiting_for_poster = State()


class BroadcastState(StatesGroup):
    """Broadcast holatlari"""
    waiting_for_message = State()
    waiting_for_confirmation = State()


class SettingsState(StatesGroup):
    """Sozlamalar holatlari"""
    waiting_for_key = State()
    waiting_for_value = State()


__all__ = [
    "SearchState",
    "AddAnimeState",
    "AddEpisodeState",
    "EditAnimeState",
    "DeleteAnimeState",
    "DeleteEpisodeState",
    "ChangePosterState",
    "BroadcastState",
    "SettingsState",
]
