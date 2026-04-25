import os
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, distinct

from app.core.database import get_db
from app.core.templates import templates
from app.models.vehicle import Vehicle

router = APIRouter()

STATIC_DIR = "app/static/img"


def _get_vehicle_image(vehicle: Vehicle) -> str:
    base_model = vehicle.model.split()[0].lower()
    model_dir = os.path.join(STATIC_DIR, "models", base_model)
    if os.path.isdir(model_dir):
        for ext in ("jpg", "jpeg", "png", "webp"):
            path = os.path.join(model_dir, f"{base_model}.{ext}")
            if os.path.isfile(path):
                return f"/static/img/models/{base_model}/{base_model}.{ext}"

    type_dir = os.path.join(STATIC_DIR, "types")
    for ext in ("jpg", "jpeg", "png", "webp"):
        path = os.path.join(type_dir, f"{vehicle.type}.{ext}")
        if os.path.isfile(path):
            return f"/static/img/types/{vehicle.type}.{ext}"

    return None


def _apply_range(stmt, column, range_value: str):
    if not range_value:
        return stmt
    try:
        if range_value.startswith("under_"):
            return stmt.where(column <= int(range_value[6:]))
        if range_value.startswith("over_"):
            return stmt.where(column >= int(range_value[5:]))
    except ValueError:
        pass
    return stmt


@router.get("/inventory/new", response_class=HTMLResponse)
async def new_vehicles(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Vehicle).where(Vehicle.condition == "new").order_by(Vehicle.price))
    vehicles = result.scalars().all()
    return templates.TemplateResponse(
        request=request,
        name="vehicle_list.html",
        context={
            "title": "New Vehicles",
            "subtitle": "Brand new 2026 models ready to drive off the lot.",
            "vehicles": vehicles,
        },
    )


@router.get("/inventory/used", response_class=HTMLResponse)
async def used_vehicles(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Vehicle).where(Vehicle.condition == "used").order_by(Vehicle.price))
    vehicles = result.scalars().all()
    return templates.TemplateResponse(
        request=request,
        name="vehicle_list.html",
        context={
            "title": "Used Vehicles",
            "subtitle": "Quality pre-owned vehicles at great prices.",
            "vehicles": vehicles,
        },
    )


@router.get("/vehicle/{vehicle_id}", response_class=HTMLResponse)
async def vehicle_detail(vehicle_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    vehicle = await db.get(Vehicle, vehicle_id)
    if not vehicle:
        return RedirectResponse(url="/")
    return templates.TemplateResponse(
        request=request,
        name="vehicle_detail.html",
        context={
            "vehicle": vehicle,
            "image_url": _get_vehicle_image(vehicle),
            "features": [f.strip() for f in vehicle.features.split(",") if f.strip()],
        },
    )


@router.get("/", response_class=HTMLResponse)
async def index(
    request: Request,
    condition: str = "",
    year: str = "",
    make: str = "",
    mileage_range: str = "",
    price_range: str = "",
    db: AsyncSession = Depends(get_db),
):
    makes_result = await db.execute(select(distinct(Vehicle.make)).order_by(Vehicle.make))
    makes = makes_result.scalars().all()

    stmt = select(Vehicle)

    if condition in ("new", "used"):
        stmt = stmt.where(Vehicle.condition == condition)

    if year:
        try:
            stmt = stmt.where(Vehicle.year == int(year))
        except ValueError:
            pass

    if make:
        stmt = stmt.where(Vehicle.make == make)

    stmt = _apply_range(stmt, Vehicle.mileage, mileage_range)
    stmt = _apply_range(stmt, Vehicle.price, price_range)

    stmt = stmt.order_by(Vehicle.condition, Vehicle.price)
    result = await db.execute(stmt)
    vehicles = result.scalars().all()

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "makes": makes,
            "vehicles": vehicles,
            "filters": {
                "condition": condition,
                "year": year,
                "make": make,
                "mileage_range": mileage_range,
                "price_range": price_range,
            },
        },
    )