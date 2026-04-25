from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import distinct

from app.core.database import get_db
from app.core.templates import templates
from app.models.vehicle import Vehicle

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def index(
    request: Request,
    condition: str = "",
    year: str = "",
    make: str = "",
    max_mileage: str = "",
    max_price: str = "",
    db: Session = Depends(get_db),
):
    makes = [r[0] for r in db.query(distinct(Vehicle.make)).order_by(Vehicle.make).all()]

    query = db.query(Vehicle)

    if condition == "new":
        query = query.filter(Vehicle.year >= 2021)
    elif condition == "used":
        query = query.filter(Vehicle.year < 2021)

    if year:
        query = query.filter(Vehicle.year == int(year))

    if make:
        query = query.filter(Vehicle.make == make)

    if max_mileage:
        query = query.filter(Vehicle.mileage <= int(max_mileage))

    if max_price:
        query = query.filter(Vehicle.price <= float(max_price))

    searched = any([condition, year, make, max_mileage, max_price])
    vehicles = query.order_by(Vehicle.year.desc()).all() if searched else []

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "makes": makes,
            "vehicles": vehicles,
            "searched": searched,
            "filters": {
                "condition": condition,
                "year": year,
                "make": make,
                "max_mileage": max_mileage,
                "max_price": max_price,
            },
        },
    )