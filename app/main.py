from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.routes import router

app = FastAPI(title="Auto Dealer Conversation Service")

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(router)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        return RedirectResponse(url="/")
    raise exc


@app.get("/health")
async def health():
    return {"status": "ok"}