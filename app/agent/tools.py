from langchain_core.tools import tool

from app.services import opensearch


@tool
async def search_vehicles(query: str) -> str:
    """Search Galaxy Motors inventory for vehicles matching the customer's needs."""
    try:
        results = await opensearch.search_vehicles(query)
    except Exception:
        return "Unable to search inventory at the moment."
    if not results:
        return "No vehicles found matching that criteria."
    lines = [
        f"- {v.get('year')} {v.get('make')} {v.get('model')}, "
        f"{v.get('condition')}, ${v.get('price'):,.0f}, {v.get('mileage'):,} miles"
        for v in results
    ]
    return "\n".join(lines)


@tool
async def express_interest(vehicle_interest: str) -> str:
    """Call this when the customer clearly wants to proceed with a specific vehicle — starts contact collection."""
    return f"Interest noted: {vehicle_interest}"