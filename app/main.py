from fastapi import FastAPI
from app.routers import auth as auth_router, movies as movies_router

app = FastAPI(title="AuraFlix")

app.include_router(auth_router.router)
app.include_router(movies_router.router)


@app.get("/")
def root():
    return {"msg": "AuraFlix API running"}
