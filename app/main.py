from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import router

app = FastAPI(title="Auto Dealer Conversation Service")

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(router)


@app.get("/health")
async def health():
    return {"status": "ok"}