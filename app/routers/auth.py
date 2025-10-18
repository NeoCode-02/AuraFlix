from fastapi import APIRouter, Depends, HTTPException, Form
from app.utils.dependencies import db_dependency
from app import schemas
from app import services
from app.config import settings
import random
import redis
from app.tasks.celery import send_verification_email_task
from app.utils.password import create_access_token, create_refresh_token
from fastapi.security import OAuth2PasswordRequestForm
from app.utils.dependencies import get_current_active_user
from app.utils.password import verify_password
from app import models
from datetime import timedelta
from app.utils.rate_limiter import rate_limit

r = redis.Redis.from_url(settings.REDIS_URL)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

CODE_TTL_SECONDS = 120  # 2 minutes


def _gen_code() -> str:
    return f"{random.randint(0, 999999):06d}"


@router.post("/register", response_model=schemas.UserOut)
async def register(user_in: schemas.UserCreate, db: db_dependency):
    existing = services.get_user_by_email(db, user_in.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = services.create_user(
        db,
        email=user_in.email,
        password=user_in.password,
        first_name=user_in.first_name,
        last_name=user_in.last_name,
    )
    code = _gen_code()
    r.setex(f"verify:{user.email}", CODE_TTL_SECONDS, code)
    send_verification_email_task.delay(user.email, code, "verify")
    return user


@router.post("/resend-code")
async def resend_code(email: str, db: db_dependency):
    rate_limit(f"resend:{email}", limit=5, window=120)  # max 5 per 2 minutes
    user = services.get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    code = _gen_code()
    r.setex(f"verify:{email}", CODE_TTL_SECONDS, code)
    send_verification_email_task.delay(email, code, "verify")
    return {"msg": "sent"}


@router.post("/verify")
async def verify(email: str, code: str, db: db_dependency):
    user = services.get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    stored = r.get(f"verify:{email}")
    if not stored:
        raise HTTPException(status_code=400, detail="Code expired or not requested")
    if stored.decode() != code:
        raise HTTPException(status_code=400, detail="Invalid code")
    services.confirm_user(db, user)
    r.delete(f"verify:{email}")
    return {"msg": "verified"}


@router.post("/login")
async def login(db: db_dependency, form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 login endpoint. Works with OAuth2PasswordBearer.
    """
    user = services.get_user_by_email(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Email not verified")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh")
async def refresh_token(refresh_token: str = Form(...)):
    from app.utils.password import decode_token

    payload = decode_token(refresh_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    new_access_token = create_access_token(data={"sub": user_id})
    return {"access_token": new_access_token, "token_type": "bearer"}


@router.get("/me")
async def get_me(current_user: models.User = Depends(get_current_active_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "is_admin": current_user.is_admin,
    }


@router.post("/password-reset/request")
async def password_reset_request(email: str, db: db_dependency):
    user = services.get_user_by_email(db, email)
    if not user:
        return {"msg": "If the email exists, a code has been sent"}
    code = _gen_code()
    r.setex(f"pwdreset:{email}", CODE_TTL_SECONDS, code)
    send_verification_email_task.delay(email, code, "reset")
    return {"msg": "If the email exists, a code has been sent"}


@router.post("/password-reset/confirm")
async def password_reset_confirm(email: str, code: str, new_password: str, db: db_dependency):
    user = services.get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    stored = r.get(f"pwdreset:{email}")
    if not stored or stored.decode() != code:
        raise HTTPException(status_code=400, detail="Invalid or expired code")
    from app.utils.password import hash_password

    user.hashed_password = hash_password(new_password)
    db.add(user)
    db.commit()
    r.delete(f"pwdreset:{email}")
    return {"msg": "password reset"}
