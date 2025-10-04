import redis
from fastapi import HTTPException, status
from app.config import settings

r = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)


def rate_limit(key: str, limit: int, window: int):
    """
    Simple fixed-window rate limiter using Redis.
    key: identifier (e.g., email)
    limit: max attempts allowed
    window: window seconds
    """
    count = r.incr(key)
    if count == 1:
        r.expire(key, window)
    if count > limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please try later.",
        )
    return True
