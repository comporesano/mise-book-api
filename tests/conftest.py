import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

import app.models  # noqa: F401  # регистрация моделей в BaseModel.metadata
from app.core.database import BaseModel, engine
from app.main import app


@pytest.fixture(autouse=True)
async def clean_db() -> None:
    """Создаёт таблицы (если их ещё нет) и очищает брони перед каждым тестом."""
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)
    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE TABLE bookings RESTART IDENTITY"))
    yield


@pytest.fixture
async def client() -> AsyncClient:
    """httpx-клиент поверх ASGI-приложения (без реального HTTP-сервера)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
