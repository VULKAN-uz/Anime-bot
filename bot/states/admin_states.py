"""
states/admin_states.py - Admin FSM holatlari
=============================================
Admin paneli uchun barcha FSM (Finite State Machine) holatlari.
"""

from aiogram.fsm.state import State, StatesGroup


class AddAnimeStates(StatesGroup):
    """Anime qo'shish holatlari."""
    waiting_code        = State()  # Kod kutish
    waiting_name        = State()  # Nom kutish
    waiting_poster      = State()  # Poster kutish
    waiting_genre       = State()  # Janr kutish
    waiting_language    = State()  # Til kutish
    waiting_description = State()  # Tavsif kutish
    waiting_episodes    = State()  # Qismlar soni kutish


class AddEpisodeStates(StatesGroup):
    """Qism qo'shish holatlari."""
    waiting_anime_code  = State()  # Anime kodi kutish
    waiting_episode_num = State()  # Qism raqami kutish
    waiting_video       = State()  # Video kutish


class EditAnimeStates(StatesGroup):
    """Anime tahrirlash holatlari."""
    waiting_anime_code  = State()  # Anime kodi
    waiting_field       = State()  # Maydon tanlash
    waiting_new_value   = State()  # Yangi qiymat


class DeleteAnimeStates(StatesGroup):
    """Anime o'chirish holatlari."""
    waiting_anime_code  = State()  # Anime kodi
    waiting_confirm     = State()  # Tasdiqlash
