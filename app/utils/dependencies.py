from app.database import SessionLocal
from fastapi import Depends
from sqlalchemy.orm import Session
from typing import Annotated
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app import models
from .password import decode_token


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def _raise_401():
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> models.User:
    payload = decode_token(token)
    if not payload:
        _raise_401()
    user_id = payload.get("sub")
    if not user_id:
        _raise_401()
    user = db.get(models.User, int(user_id))
    if not user:
        _raise_401()
    return user


def get_current_active_user(current_user: models.User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    if not current_user.is_verified:
        raise HTTPException(status_code=403, detail="Email not verified")
    return current_user


def get_current_admin_user(
    current_user: models.User = Depends(get_current_active_user),
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Requires admin privileges")
    return current_user
