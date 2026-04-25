from fastapi import APIRouter

from app.api import inventory, pages

router = APIRouter()

router.include_router(inventory.router)
router.include_router(pages.router)