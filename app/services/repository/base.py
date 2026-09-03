from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Generic, TypeVar, overload

from sqlalchemy import delete, insert, select, update

from app.core.database import BaseModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
else:
    AsyncSession = object

SQLModelType = TypeVar("SQLModelType", bound=BaseModel)


def _affected_rows(result: Any) -> int:
    """Количество затронутых строк; rowcount может быть -1, если драйвер его не сообщил."""
    rowcount = getattr(result, "rowcount", 0) or 0
    return max(0, rowcount)


class BaseRepository(Generic[SQLModelType]):
    model: type[SQLModelType]

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @overload
    async def get(self, id: None = None) -> Sequence[SQLModelType]: ...

    @overload
    async def get(self, id: int) -> SQLModelType | None: ...

    async def get(self, id: int | None = None):
        """Метод get для репозитория."""
        query = select(self.model)
        if id is not None:
            query = query.where(self.model.id == id)
            result = await self._session.execute(query)
            return result.scalar_one_or_none()
        else:
            result = await self._session.execute(query)
            return result.scalars().all()

    async def get_by(self, **filters: Any) -> SQLModelType | None:
        """Получить первую запись по фильтрам."""
        query = select(self.model)
        for field, value in filters.items():
            query = query.where(getattr(self.model, field) == value)

        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def filter(self, **filters: Any) -> Sequence[SQLModelType]:
        """Получить все записи по фильтрам."""
        query = select(self.model)
        for field, value in filters.items():
            query = query.where(getattr(self.model, field) == value)

        result = await self._session.execute(query)
        return result.scalars().all()

    async def exists(self, **filters: Any) -> bool:
        """Проверить существование записи."""
        query = select(self.model.id)
        for field, value in filters.items():
            query = query.where(getattr(self.model, field) == value)

        result = await self._session.execute(query.limit(1))
        return result.first() is not None

    async def count(self, **filters: Any) -> int:
        """Посчитать количество записей по фильтрам."""
        from sqlalchemy import func

        query = select(func.count()).select_from(self.model)
        for field, value in filters.items():
            query = query.where(getattr(self.model, field) == value)

        result = await self._session.execute(query)
        return result.scalar() or 0

    # ========== CREATE ==========

    async def create(self, **kwargs: Any) -> SQLModelType:
        """Создать новую запись."""
        instance = self.model(**kwargs)
        self._session.add(instance)
        await self._session.commit()
        await self._session.refresh(instance)
        return instance

    async def create_many(self, items: list[dict[str, Any]]) -> Sequence[SQLModelType]:
        """Создать несколько записей."""
        instances = [self.model(**item) for item in items]
        self._session.add_all(instances)
        await self._session.commit()
        for instance in instances:
            await self._session.refresh(instance)
        return instances

    async def get_or_create(
        self,
        defaults: dict[str, Any] | None = None,
        **filters: Any,
    ) -> tuple[SQLModelType, bool]:
        """
        Получить запись или создать новую.
        Возвращает (запись, создана_ли_новая).
        """
        instance = await self.get_by(**filters)
        if instance:
            return instance, False

        create_data = {**filters, **(defaults or {})}
        instance = await self.create(**create_data)
        return instance, True

    # ========== UPDATE ==========

    async def update(self, id: int, **kwargs: Any) -> SQLModelType | None:
        """Обновить запись по ID."""
        await self._session.execute(
            update(self.model)
            .where(self.model.id == id)
            .values(**kwargs)
        )
        await self._session.commit()
        return await self.get(id)

    async def update_by(
        self,
        filters: dict[str, Any],
        **kwargs: Any,
    ) -> int:
        """
        Обновить записи по фильтрам.
        Возвращает количество обновлённых записей.
        """
        query = update(self.model)
        for field, value in filters.items():
            query = query.where(getattr(self.model, field) == value)

        result = await self._session.execute(query.values(**kwargs))
        await self._session.commit()
        return _affected_rows(result)

    async def update_or_create(
        self,
        defaults: dict[str, Any],
        **filters: Any,
    ) -> tuple[SQLModelType, bool]:
        """
        Обновить запись или создать новую.
        Возвращает (запись, создана_ли_новая).
        """
        instance = await self.get_by(**filters)
        if instance:
            updated = await self.update(instance.id, **defaults)
            return updated if updated is not None else instance, False

        create_data = {**filters, **defaults}
        instance = await self.create(**create_data)
        return instance, True

    # ========== DELETE ==========

    async def delete(self, id: int) -> bool:
        """Удалить запись по ID."""
        result = await self._session.execute(
            delete(self.model).where(self.model.id == id)
        )
        await self._session.commit()
        return _affected_rows(result) > 0

    async def delete_by(self, **filters: Any) -> int:
        """
        Удалить записи по фильтрам.
        Возвращает количество удалённых записей.
        """
        query = delete(self.model)
        for field, value in filters.items():
            query = query.where(getattr(self.model, field) == value)

        result = await self._session.execute(query)
        await self._session.commit()
        return _affected_rows(result)

    async def delete_all(self) -> int:
        """Удалить все записи."""
        result = await self._session.execute(delete(self.model))
        await self._session.commit()
        return _affected_rows(result)

    # ========== BULK OPERATIONS ==========

    async def bulk_create(self, items: list[dict[str, Any]]) -> None:
        """Массовое создание (быстрее, но не возвращает объекты)."""
        await self._session.execute(
            insert(self.model),
            items,
        )
        await self._session.commit()

    async def bulk_update(self, items: list[dict[str, Any]]) -> None:
        """Массовое обновление по ID."""
        for item in items:
            if 'id' not in item:
                raise ValueError("Each item must have 'id' for bulk update")
            await self._session.execute(
                update(self.model)
                .where(self.model.id == item.pop('id'))
                .values(**item)
            )
        await self._session.commit()

    async def bulk_delete(self, ids: list[int]) -> int:
        """Массовое удаление по списку ID."""
        result = await self._session.execute(
            delete(self.model).where(self.model.id.in_(ids))
        )
        await self._session.commit()
        return _affected_rows(result)
