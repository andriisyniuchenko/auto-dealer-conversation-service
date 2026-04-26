import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.core.database import Base, get_db
from app.main import app
from app.models.vehicle import Vehicle

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

test_engine = create_async_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})


@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_test_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db():
    async with AsyncSession(test_engine) as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db):
    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def sample_vehicle(db):
    vehicle = Vehicle(
        id="test-vehicle-001",
        make="Subaru",
        model="Forester Limited",
        year=2026,
        type="suv",
        transmission="automatic",
        mileage=5,
        price=35000.0,
        color="white",
        engine="2.5L 4-cylinder",
        origin="japanese",
        features="AWD, Heated Seats, Sunroof",
        condition="new",
    )
    db.add(vehicle)
    await db.flush()
    return vehicle