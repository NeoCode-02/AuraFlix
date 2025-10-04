from sqlalchemy import select
from sqlalchemy.orm import Session
from app import models
from app.utils.password import hash_password, verify_password


def get_user_by_email(db: Session, email: str):
    return db.execute(
        select(models.User).where(models.User.email == email)
    ).scalar_one_or_none()


def create_user(
    db: Session,
    email: str,
    password: str,
    first_name: str = None,
    last_name: str = None,
):
    hashed = hash_password(password)
    user = models.User(
        email=email, hashed_password=hashed, first_name=first_name, last_name=last_name
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def verify_user_password(user: models.User, password: str):
    return verify_password(password, user.hashed_password)


def confirm_user(db: Session, user: models.User):
    user.is_verified = True
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_movie(db: Session, movie_id: int):
    return db.get(models.Movie, movie_id)


def list_movies(db: Session, skip: int = 0, limit: int = 50):
    return db.execute(select(models.Movie).offset(skip).limit(limit)).scalars().all()


def create_movie(db: Session, **data):
    movie = models.Movie(**data)
    db.add(movie)
    db.commit()
    db.refresh(movie)
    return movie


def increment_view_count(db: Session, movie: models.Movie):
    movie.view_count = (movie.view_count or 0) + 1
    db.add(movie)
    db.commit()
    db.refresh(movie)
    return movie
