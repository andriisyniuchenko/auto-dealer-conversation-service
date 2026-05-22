import httpx

from app.core.config import settings
from app.schemas.lead import LeadFormData

_HEADERS = {"X-API-Key": settings.crm_api_key}
_LEADS_URL = f"{settings.crm_api_url}/api/v1/leads/public"
_CHAT_SESSIONS_URL = f"{settings.crm_api_url}/api/v1/chat/sessions"


async def submit_lead(form: LeadFormData) -> bool:
    payload = {
        "first_name": form.first_name,
        "last_name": form.last_name,
        "phone": form.phone,
        "source": "website",
        "interest": form.vehicle_label,
    }
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(_LEADS_URL, json=payload, headers=_HEADERS)
            return response.is_success
    except httpx.HTTPError:
        return False


async def submit_lead_from_chat(
    first_name: str,
    last_name: str,
    phone: str,
    interest: str,
    email: str | None = None,
    notes: str | None = None,
) -> int | None:
    payload = {
        "first_name": first_name,
        "last_name": last_name,
        "phone": phone,
        "source": "AI Chat Widget",
        "interest": interest,
        "email": email,
        "notes": notes,
    }
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(_LEADS_URL, json=payload, headers=_HEADERS)
            if response.is_success:
                return response.json().get("lead_id")
            return None
    except httpx.HTTPError:
        return None


async def book_appointment(lead_id: int, appointment_at: str, notes: str | None = None) -> bool:
    payload = {"lead_id": lead_id, "appointment_at": appointment_at, "notes": notes}
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{settings.crm_api_url}/api/v1/leads/public/appointments",
                json=payload,
                headers=_HEADERS,
            )
            return response.is_success
    except httpx.HTTPError:
        return False


async def save_chat_session(session_id: str, messages: list[dict], lead_id: int | None = None) -> bool:
    import logging
    logger = logging.getLogger(__name__)
    payload = {"session_id": session_id, "messages": messages, "lead_id": lead_id}
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(_CHAT_SESSIONS_URL, json=payload, headers=_HEADERS)
            if not response.is_success:
                logger.error("save_chat_session failed: %s %s", response.status_code, response.text)
            return response.is_success
    except httpx.HTTPError as e:
        logger.error("save_chat_session HTTP error: %s", e)
        return False