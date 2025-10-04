import os
from decouple import config


class Settings:
    APP_HOST: str = config("APP_HOST", default="0.0.0.0")
    APP_PORT: int = config("APP_PORT", default=8000, cast=int)
    SECRET_KEY: str = config("SECRET_KEY", default="change_me")
    ALGORITHM: str = config("ALGORITHM", default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = config(
        "ACCESS_TOKEN_EXPIRE_MINUTES", default=15, cast=int
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = config(
        "REFRESH_TOKEN_EXPIRE_DAYS", default=30, cast=int
    )
    DATABASE_URL: str = config("DATABASE_URL")
    REDIS_URL: str = config("REDIS_URL", default="redis://localhost:6379/0")
    CELERY_BROKER_URL: str = config("CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: str = config("CELERY_RESULT_BACKEND")
    SMTP_HOST: str = config("SMTP_HOST")
    SMTP_PORT: int = config("SMTP_PORT", default=587, cast=int)
    SMTP_USER: str = config("SMTP_USER")
    SMTP_PASSWORD: str = config("SMTP_PASSWORD")
    SMTP_FROM: str = config("SMTP_FROM")
    MEDIA_DIR: str = config("MEDIA_DIR", default="./app/media")
    MAX_VIDEO_UPLOAD_BYTES: int = int(os.getenv("MAX_VIDEO_UPLOAD_BYTES", 0)) or None


settings = Settings()
