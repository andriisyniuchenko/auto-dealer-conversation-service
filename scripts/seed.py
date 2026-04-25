import json
import os
import sys

import chromadb

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.core.database import SessionLocal
from app.models.vehicle import Vehicle

CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", 8000))
INVENTORY_PATH = os.path.join(os.path.dirname(__file__), "../app/data/inventory.json")


def build_chroma_document(car: dict) -> str:
    features = ", ".join(car.get("features", []))
    return (
        f"{car['year']} {car['make']} {car['model']}, "
        f"{car['type']}, {car['transmission']}, "
        f"{car['mileage']} miles, ${car['price']}, "
        f"color: {car['color']}, engine: {car['engine']}, "
        f"origin: {car['origin']}, features: {features}"
    )


def seed_postgres(inventory: list):
    db = SessionLocal()
    try:
        for v in inventory:
            vehicle = db.get(Vehicle, v["id"])
            if vehicle:
                vehicle.condition = v["condition"]
            else:
                db.add(Vehicle(
                    id=v["id"],
                    make=v["make"],
                    model=v["model"],
                    year=v["year"],
                    type=v["type"],
                    transmission=v["transmission"],
                    mileage=v["mileage"],
                    price=v["price"],
                    color=v["color"],
                    engine=v["engine"],
                    origin=v["origin"],
                    features=", ".join(v.get("features", [])),
                    condition=v["condition"],
                ))
        db.commit()
        print(f"PostgreSQL: upserted {len(inventory)} vehicles.")
    finally:
        db.close()


def seed_chromadb(inventory: list):
    client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
    collection = client.get_or_create_collection("inventory")
    collection.upsert(
        documents=[build_chroma_document(v) for v in inventory],
        ids=[v["id"] for v in inventory],
        metadatas=[
            {
                "make": v["make"],
                "model": v["model"],
                "year": v["year"],
                "price": v["price"],
                "mileage": v["mileage"],
                "origin": v["origin"],
                "type": v["type"],
            }
            for v in inventory
        ],
    )
    print(f"ChromaDB: seeded {len(inventory)} vehicles.")


if __name__ == "__main__":
    with open(INVENTORY_PATH) as f:
        inventory = json.load(f)

    seed_postgres(inventory)
    seed_chromadb(inventory)