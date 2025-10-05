from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routers import auth as auth_router, movies as movies_router
from app.admin.setup import admin
from app.config import settings
import os

app = FastAPI(title="AuraFlix")

app.mount(
    "/media",
    StaticFiles(directory=os.path.join(settings.MEDIA_DIR)),
    name="media",
)

app.include_router(auth_router.router)
app.include_router(movies_router.router)


@app.get("/")
def root():
    return {"msg": "AuraFlix API running"}


admin.mount_to(app)
