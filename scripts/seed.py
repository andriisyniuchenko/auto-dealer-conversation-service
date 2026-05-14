import json
import os
import sys

import requests
from opensearchpy import OpenSearch, helpers
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.core.config import settings
from app.models.vehicle import Vehicle

_engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(bind=_engine)

INVENTORY_PATH = os.path.join(os.path.dirname(__file__), "../app/data/inventory.json")
OPENSEARCH_INDEX = "vehicles"
EMBEDDING_MODEL = "nomic-embed-text"
EMBEDDING_DIM = 768

INDEX_MAPPING = {
    "settings": {"index": {"knn": True}},
    "mappings": {
        "properties": {
            "vector": {"type": "knn_vector", "dimension": EMBEDDING_DIM},
            "text": {"type": "text"},
            "vehicle_id": {"type": "keyword"},
            "make": {"type": "keyword"},
            "model": {"type": "keyword"},
            "condition": {"type": "keyword"},
            "year": {"type": "integer"},
            "price": {"type": "float"},
            "mileage": {"type": "integer"},
            "type": {"type": "keyword"},
        }
    },
}


def build_document_text(car: dict) -> str:
    features = ", ".join(car.get("features", []))
    trim = f" {car['trim']}" if car.get("trim") else ""
    return (
        f"{car['year']} {car['make']} {car['model']}{trim}, "
        f"{car['condition']} {car['type']}, {car['transmission']}, "
        f"{car['mileage']} miles, ${car['price']}, "
        f"color: {car['color']}, engine: {car['engine']}, "
        f"origin: {car['origin']}, features: {features}"
    )


def get_embedding(text: str) -> list[float]:
    response = requests.post(
        f"{settings.ollama_base_url}/api/embed",
        json={"model": EMBEDDING_MODEL, "input": text},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["embeddings"][0]


def seed_postgres(inventory: list):
    db = SessionLocal()
    try:
        for v in inventory:
            vehicle = db.get(Vehicle, v["id"])
            if vehicle:
                vehicle.condition = v["condition"]
                vehicle.model = v["model"]
                vehicle.trim = v.get("trim")
            else:
                db.add(Vehicle(
                    id=v["id"],
                    make=v["make"],
                    model=v["model"],
                    trim=v.get("trim"),
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


def seed_opensearch(inventory: list):
    client = OpenSearch(settings.opensearch_url)

    if client.indices.exists(index=OPENSEARCH_INDEX):
        client.indices.delete(index=OPENSEARCH_INDEX)
    client.indices.create(index=OPENSEARCH_INDEX, body=INDEX_MAPPING)
    print(f"OpenSearch: created index '{OPENSEARCH_INDEX}'.")

    actions = []
    for i, v in enumerate(inventory):
        text = build_document_text(v)
        try:
            vector = get_embedding(text)
        except Exception as e:
            print(f"  Embedding failed for vehicle {v['id']}: {e}")
            continue

        actions.append({
            "_index": OPENSEARCH_INDEX,
            "_id": v["id"],
            "_source": {
                "vector": vector,
                "text": text,
                "vehicle_id": v["id"],
                "make": v["make"],
                "model": v["model"],
                "condition": v["condition"],
                "year": v["year"],
                "price": v["price"],
                "mileage": v["mileage"],
                "type": v["type"],
            },
        })
        print(f"  Embedded {i + 1}/{len(inventory)}: {v['year']} {v['make']} {v['model']}")

    if actions:
        helpers.bulk(client, actions)
        print(f"OpenSearch: indexed {len(actions)} vehicles.")


if __name__ == "__main__":
    with open(INVENTORY_PATH) as f:
        inventory = json.load(f)

    seed_postgres(inventory)
    seed_opensearch(inventory)