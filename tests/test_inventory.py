import pytest


@pytest.mark.asyncio
async def test_homepage_returns_200(client):
    response = await client.get("/")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_homepage_shows_vehicles(client, sample_vehicle):
    response = await client.get("/")
    assert response.status_code == 200
    assert sample_vehicle.make in response.text


@pytest.mark.asyncio
async def test_new_vehicles_page(client, sample_vehicle):
    response = await client.get("/inventory/new")
    assert response.status_code == 200
    assert sample_vehicle.model in response.text


@pytest.mark.asyncio
async def test_used_vehicles_page(client):
    response = await client.get("/inventory/used")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_vehicle_detail_returns_200(client, sample_vehicle):
    response = await client.get(f"/vehicle/{sample_vehicle.id}")
    assert response.status_code == 200
    assert sample_vehicle.make in response.text
    assert sample_vehicle.model in response.text


@pytest.mark.asyncio
async def test_vehicle_detail_unknown_id_redirects(client):
    response = await client.get("/vehicle/nonexistent-id", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/"


@pytest.mark.asyncio
async def test_unknown_route_redirects(client):
    response = await client.get("/this-page-does-not-exist", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/"


@pytest.mark.asyncio
async def test_filter_by_condition(client, sample_vehicle):
    response = await client.get("/?condition=new")
    assert response.status_code == 200
    assert sample_vehicle.make in response.text


@pytest.mark.asyncio
async def test_filter_by_make(client, sample_vehicle):
    response = await client.get(f"/?make={sample_vehicle.make}")
    assert response.status_code == 200
    assert sample_vehicle.make in response.text


@pytest.mark.asyncio
async def test_filter_invalid_price_range_does_not_crash(client):
    response = await client.get("/?price_range=over_abc")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_check(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}