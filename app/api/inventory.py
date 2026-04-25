import os
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import distinct

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


@router.get("/vehicle/{vehicle_id}", response_class=HTMLResponse)
def vehicle_detail(vehicle_id: str, request: Request, db: Session = Depends(get_db)):
    vehicle = db.get(Vehicle, vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return templates.TemplateResponse(
        request=request,
        name="vehicle_detail.html",
        context={
            "vehicle": vehicle,
            "image_url": _get_vehicle_image(vehicle),
            "features": [f.strip() for f in vehicle.features.split(",") if f.strip()],
        },
    )


def _apply_range(query, column, range_value: str):
    if not range_value:
        return query
    if range_value.startswith("under_"):
        return query.filter(column <= int(range_value[6:]))
    if range_value.startswith("over_"):
        return query.filter(column >= int(range_value[5:]))
    return query


@router.get("/inventory/new", response_class=HTMLResponse)
def new_vehicles(request: Request, db: Session = Depends(get_db)):
    vehicles = db.query(Vehicle).filter(Vehicle.condition == "new").order_by(Vehicle.price).all()
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
def used_vehicles(request: Request, db: Session = Depends(get_db)):
    vehicles = db.query(Vehicle).filter(Vehicle.condition == "used").order_by(Vehicle.price).all()
    return templates.TemplateResponse(
        request=request,
        name="vehicle_list.html",
        context={
            "title": "Used Vehicles",
            "subtitle": "Quality pre-owned vehicles at great prices.",
            "vehicles": vehicles,
        },
    )


@router.get("/", response_class=HTMLResponse)
def index(
    request: Request,
    condition: str = "",
    year: str = "",
    make: str = "",
    mileage_range: str = "",
    price_range: str = "",
    db: Session = Depends(get_db),
):
    makes = [r[0] for r in db.query(distinct(Vehicle.make)).order_by(Vehicle.make).all()]

    query = db.query(Vehicle)

    if condition in ("new", "used"):
        query = query.filter(Vehicle.condition == condition)

    if year:
        try:
            query = query.filter(Vehicle.year == int(year))
        except ValueError:
            pass

    if make:
        query = query.filter(Vehicle.make == make)

    query = _apply_range(query, Vehicle.mileage, mileage_range)
    query = _apply_range(query, Vehicle.price, price_range)

    vehicles = query.order_by(Vehicle.condition, Vehicle.price).all()

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