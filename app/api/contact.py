from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.inventory import _get_vehicle_image
from app.core.database import get_db
from app.core.templates import templates
from app.models.vehicle import Vehicle
from app.schemas.lead import LeadFormData
from app.services.crm import submit_lead

router = APIRouter()


async def _render_detail(request: Request, vehicle: Vehicle, form_error: str = None, form_success: bool = False):
    features = [f.strip() for f in vehicle.features.split(",") if f.strip()]
    return templates.TemplateResponse(
        request=request,
        name="vehicle_detail.html",
        context={
            "vehicle": vehicle,
            "image_url": _get_vehicle_image(vehicle),
            "features": features,
            "form_error": form_error,
            "form_success": form_success,
        },
    )


@router.post("/contact", response_class=HTMLResponse)
async def contact(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    phone: str = Form(...),
    vehicle_id: str = Form(...),
    vehicle_label: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    vehicle = await db.get(Vehicle, vehicle_id)
    if not vehicle:
        return RedirectResponse(url="/", status_code=303)

    try:
        form = LeadFormData(
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            vehicle_id=vehicle_id,
            vehicle_label=vehicle_label,
        )
    except ValidationError:
        return await _render_detail(request, vehicle, form_error="Please check your phone number and try again.")

    success = await submit_lead(form)

    if success:
        return RedirectResponse(url=f"/vehicle/{vehicle_id}?success=1", status_code=303)

    return await _render_detail(request, vehicle, form_error="Something went wrong. Please try again or call us directly.")