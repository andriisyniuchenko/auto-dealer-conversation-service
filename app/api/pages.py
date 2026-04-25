from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.core.templates import templates

router = APIRouter()


@router.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    return templates.TemplateResponse(request=request, name="about.html")


@router.get("/parts-service", response_class=HTMLResponse)
async def parts_service(request: Request):
    return templates.TemplateResponse(request=request, name="parts_service.html")