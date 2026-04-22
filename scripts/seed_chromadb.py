import json
import os
import chromadb

CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", 8000))

INVENTORY_PATH = os.path.join(os.path.dirname(__file__), "../app/data/inventory.json")


def build_document(car: dict) -> str:
    features = ", ".join(car.get("features", []))
    return (
        f"{car['year']} {car['make']} {car['model']}, "
        f"{car['type']}, {car['transmission']}, "
        f"{car['mileage']} miles, ${car['price']}, "
        f"color: {car['color']}, engine: {car['engine']}, "
        f"origin: {car['origin']}, features: {features}"
    )


def seed():
    with open(INVENTORY_PATH) as f:
        inventory = json.load(f)

    client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)

    collection = client.get_or_create_collection("inventory")

    documents = [build_document(car) for car in inventory]
    ids = [car["id"] for car in inventory]
    metadatas = [
        {
            "make": car["make"],
            "model": car["model"],
            "year": car["year"],
            "price": car["price"],
            "mileage": car["mileage"],
            "origin": car["origin"],
            "type": car["type"],
        }
        for car in inventory
    ]

    collection.upsert(documents=documents, ids=ids, metadatas=metadatas)
    print(f"Loaded {len(inventory)} vehicles into ChromaDB.")


if __name__ == "__main__":
    seed()