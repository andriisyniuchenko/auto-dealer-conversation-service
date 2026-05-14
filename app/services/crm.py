import httpx

from app.core.config import settings
from app.schemas.lead import LeadFormData

_HEADERS = {"X-API-Key": settings.crm_api_key}
_LEADS_URL = f"{settings.crm_api_url}/api/v1/leads/public"


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
) -> bool:
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
            return response.is_success
    except httpx.HTTPError:
        return False