from celery import Celery
from app.database import SessionLocal
from app import services
from app.config import settings
from app.tasks.email import send_email


celery_app = Celery(
    "auraflix",
    broker=settings.CELERY_BROKER_URL or "redis://localhost:6379/1",
    backend=settings.CELERY_RESULT_BACKEND or "redis://localhost:6379/2",
)


@celery_app.task
def send_verification_email_task(to_email: str, code: str, purpose: str = "verify"):
    subject = (
        f"AuraFlix {'Verification' if purpose == 'verify' else 'Password Reset'} Code"
    )
    body = f"Your AuraFlix {'verification' if purpose == 'verify' else 'password reset'} code is: {code}\nThis code expires in 10 minutes."
    send_email(to_email, subject, body)
    return True


@celery_app.task
def increment_view_count_task(movie_id: int):
    db = SessionLocal()
    try:
        movie = services.get_movie(db, movie_id)
        if movie:
            services.increment_view_count(db, movie)
    finally:
        db.close()
