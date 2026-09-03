from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class BaseModel(DeclarativeBase):
    """Базовый класс для ORM-моделей приложения."""


engine = create_async_engine(settings.database_url, echo=settings.debug)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Метод для инжектирования бдшки."""
    async with async_session_maker() as session:
        yield session
