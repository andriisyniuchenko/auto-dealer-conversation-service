import httpx

from app.core.config import settings
from app.schemas.lead import LeadFormData


async def submit_lead(form: LeadFormData) -> bool:
    payload = {
        "first_name": form.first_name,
        "last_name": form.last_name,
        "phone": form.phone,
        "source": "website",
        "interest": form.vehicle_label,
    }
    headers = {"X-API-Key": settings.crm_api_key}

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{settings.crm_api_url}/api/v1/leads/public",
                json=payload,
                headers=headers,
            )
            return response.is_success
    except httpx.HTTPError:
        return False