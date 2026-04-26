import pytest
from unittest.mock import patch, AsyncMock


@pytest.mark.asyncio
async def test_contact_crm_unavailable_shows_error(client, sample_vehicle):
    with patch("app.api.contact.submit_lead", new_callable=AsyncMock, return_value=False):
        response = await client.post("/contact", data={
            "first_name": "John",
            "last_name": "Doe",
            "phone": "1234567890",
            "vehicle_id": sample_vehicle.id,
            "vehicle_label": "2026 Subaru Forester Limited",
        })
    assert response.status_code == 200
    assert "Something went wrong" in response.text


@pytest.mark.asyncio
async def test_contact_success_redirects(client, sample_vehicle):
    with patch("app.api.contact.submit_lead", new_callable=AsyncMock, return_value=True):
        response = await client.post("/contact", data={
            "first_name": "John",
            "last_name": "Doe",
            "phone": "1234567890",
            "vehicle_id": sample_vehicle.id,
            "vehicle_label": "2026 Subaru Forester Limited",
        }, follow_redirects=False)
    assert response.status_code == 303
    assert f"/vehicle/{sample_vehicle.id}" in response.headers["location"]


@pytest.mark.asyncio
async def test_contact_invalid_phone_shows_error(client, sample_vehicle):
    with patch("app.api.contact.submit_lead", new_callable=AsyncMock, return_value=False):
        response = await client.post("/contact", data={
            "first_name": "John",
            "last_name": "Doe",
            "phone": "abc",
            "vehicle_id": sample_vehicle.id,
            "vehicle_label": "2026 Subaru Forester Limited",
        })
    assert response.status_code == 200
    assert "Please check your phone number" in response.text


@pytest.mark.asyncio
async def test_contact_unknown_vehicle_redirects_home(client):
    response = await client.post("/contact", data={
        "first_name": "John",
        "last_name": "Doe",
        "phone": "1234567890",
        "vehicle_id": "nonexistent-id",
        "vehicle_label": "Unknown",
    }, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/"