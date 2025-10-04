from sqlalchemy import Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from app.database import Base
from typing import Optional
from datetime import datetime


class TimeMixin:
    __abstract__ = True

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )


class User(Base, TimeMixin):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    first_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)


class Genre(Base, TimeMixin):
    __tablename__ = "genres"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)

    movies: Mapped[list["Movie"]] = relationship("Movie", back_populates="genre")


class Movie(Base, TimeMixin):
    __tablename__ = "movies"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    genre_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("genres.id"), nullable=True
    )
    language: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    duration: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    poster_path: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    release_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    genre: Mapped[Optional["Genre"]] = relationship("Genre", back_populates="movies")
