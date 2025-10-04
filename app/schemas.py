from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserOut(BaseModel):
    id: int
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_verified: bool
    is_active: bool

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: Optional[str] = None


class MovieCreate(BaseModel):
    title: str
    description: Optional[str] = None
    genre_id: Optional[int] = None
    language: Optional[str] = None
    duration: Optional[int] = None
    file_path: str
    poster_path: Optional[str] = None
    release_date: Optional[datetime] = None


class MovieOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    genre_id: Optional[int]
    language: Optional[str]
    duration: Optional[int]
    poster_path: Optional[str]
    view_count: int
    file_path: str
    release_date: Optional[datetime]

    class Config:
        from_attributes = True


class GenreCreate(BaseModel):
    name: str


class GenreOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True
