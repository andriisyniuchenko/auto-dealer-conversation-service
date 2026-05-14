from fastapi import APIRouter

from app.api import chat, contact, inventory, pages

router = APIRouter()

router.include_router(inventory.router)
router.include_router(pages.router)
router.include_router(contact.router)
router.include_router(chat.router)