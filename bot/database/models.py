"""
database/models.py - SQLAlchemy modellari
==========================================
Barcha jadval modellari shu yerda aniqlanadi.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Asosiy model sinfi"""
    pass


class User(Base):
    """Foydalanuvchilar jadvali"""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_subscribed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    language: Mapped[str] = mapped_column(String(10), default="uz", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    last_activity: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
    searches_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Bog'liqliklar
    favorites: Mapped[list["Favorite"]] = relationship(
        "Favorite", back_populates="user", cascade="all, delete-orphan"
    )
    search_history: Mapped[list["SearchHistory"]] = relationship(
        "SearchHistory", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(user_id={self.user_id}, full_name={self.full_name!r})>"


class Anime(Base):
    """Animeler jadvali"""
    __tablename__ = "animes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[int] = mapped_column(Integer, unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    name_en: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    poster_file_id: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    genre: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    duration: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    language: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    rating: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    episodes_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="ongoing", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    searches_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    views_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Bog'liqliklar
    episodes: Mapped[list["Episode"]] = relationship(
        "Episode", back_populates="anime", cascade="all, delete-orphan",
        order_by="Episode.episode_number"
    )
    favorites: Mapped[list["Favorite"]] = relationship(
        "Favorite", back_populates="anime", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Anime(code={self.code}, name={self.name!r})>"


class Episode(Base):
    """Qismlar jadvali"""
    __tablename__ = "episodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    anime_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("animes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    episode_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    file_id: Mapped[str] = mapped_column(String(500), nullable=False)
    file_unique_id: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    duration: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # sekundlarda
    file_size: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)  # baytlarda
    views_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    downloads_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    # Bog'liqliklar
    anime: Mapped["Anime"] = relationship("Anime", back_populates="episodes")

    def __repr__(self) -> str:
        return f"<Episode(anime_id={self.anime_id}, ep={self.episode_number})>"


class Favorite(Base):
    """Sevimlilar jadvali"""
    __tablename__ = "favorites"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    anime_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("animes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    # Bog'liqliklar
    user: Mapped["User"] = relationship("User", back_populates="favorites")
    anime: Mapped["Anime"] = relationship("Anime", back_populates="favorites")

    def __repr__(self) -> str:
        return f"<Favorite(user_id={self.user_id}, anime_id={self.anime_id})>"


class SearchHistory(Base):
    """Qidiruv tarixi"""
    __tablename__ = "search_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    query: Mapped[str] = mapped_column(String(500), nullable=False)
    anime_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    found: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    # Bog'liqliklar
    user: Mapped["User"] = relationship("User", back_populates="search_history")

    def __repr__(self) -> str:
        return f"<SearchHistory(user_id={self.user_id}, query={self.query!r})>"


class BroadcastMessage(Base):
    """Broadcast xabarlari tarixi"""
    __tablename__ = "broadcast_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    admin_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    message_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    media_file_id: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    media_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    sent_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<BroadcastMessage(id={self.id}, status={self.status!r})>"


class BotSettings(Base):
    """Bot sozlamalari"""
    __tablename__ = "bot_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<BotSettings(key={self.key!r}, value={self.value!r})>"
