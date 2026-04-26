from fastapi import APIRouter

from app.api import inventory, pages, contact

router = APIRouter()

router.include_router(inventory.router)
router.include_router(pages.router)
router.include_router(contact.router)