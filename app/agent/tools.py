from langchain_core.tools import tool

from app.services import crm, opensearch


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
async def submit_lead(
    first_name: str,
    last_name: str,
    phone: str,
    interest: str,
    email: str = "",
    notes: str = "",
) -> str:
    """Submit a customer lead to the CRM when they want to be contacted by a sales rep."""
    lead_id = await crm.submit_lead_from_chat(
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        interest=interest,
        email=email or None,
        notes=notes or None,
    )
    if lead_id:
        return f"Lead submitted for {first_name} {last_name}. crm_lead_id={lead_id}"
    return "Failed to pass customer details. Please try again."