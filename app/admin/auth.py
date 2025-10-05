from datetime import datetime, timedelta, UTC
from fastapi import Request, Response
from jose import jwt, JWTError, ExpiredSignatureError
from sqlalchemy.orm import Session
from starlette_admin.auth import AuthProvider
from starlette_admin.exceptions import LoginFailed

from app.models import User
from app.utils.dependencies import get_db
from app.utils.password import verify_password
from app.config import settings


class JSONAuthProvider(AuthProvider):
    async def login(
        self,
        email: str,
        password: str,
        remember_me: bool,
        request: Request,
        response: Response,
    ):
        """Authenticate admin user and set JWT cookie."""
        db: Session = next(get_db())
        user = db.query(User).filter(User.email == email).first()

        if not user or not user.is_admin:
            raise LoginFailed("Invalid admin credentials.")

        if not verify_password(password, user.hashed_password):
            raise LoginFailed("Incorrect password.")

        token_data = {
            "sub": user.email,
            "exp": datetime.now(UTC)
            + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        }
        token = jwt.encode(
            token_data, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )

        response.set_cookie(
            key="access_token",
            value=token,
            httponly=True,
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            secure=False,
            samesite="lax",
        )
        return response

    async def is_authenticated(self, request: Request) -> User | None:
        """Check if request has a valid admin JWT cookie."""
        token = request.cookies.get("access_token")
        if not token:
            return None

        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            email = payload.get("sub")
            exp = payload.get("exp")

            if not email or exp < datetime.now(UTC).timestamp():
                return None

            db: Session = next(get_db())
            user = db.query(User).filter(User.email == email).first()

            if user and user.is_admin:
                return user

        except (JWTError, ExpiredSignatureError):
            return None

        return None

    async def logout(self, request: Request, response: Response):
        """Remove JWT cookie on logout."""
        response.delete_cookie("access_token")
        return response
