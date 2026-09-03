from datetime import date, time

from sqlalchemy import select

from app.core.exceptions import BookingNotFoundError, SlotAlreadyTakenError
from app.models import Booking, BookingStatus
from app.services.repository.base import BaseRepository


class BookingRepository(BaseRepository[Booking]):
    """Репозиторий броней."""

    model = Booking

    async def get_all(self, booking_date: date | None = None) -> list[Booking]:
        """Все брони, опционально по дате, в хронологическом порядке."""
        query = select(self.model).order_by(self.model.booking_date, self.model.booking_time)
        if booking_date is not None:
            query = query.where(self.model.booking_date == booking_date)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def get_active_by_slot(self, booking_date: date, booking_time: time) -> Booking | None:
        """Активная бронь на конкретные дату и время (проверка занятости слота)."""
        return await self.get_by(
            booking_date=booking_date,
            booking_time=booking_time,
            status=BookingStatus.active,
        )

    async def create_booking(
        self, *, name: str, phone: str, booking_date: date, booking_time: time, guests: int
    ) -> Booking:
        """Создаёт бронь; если слот занят активной бронью - SlotAlreadyTakenError."""
        existing = await self.get_active_by_slot(booking_date, booking_time)
        if existing is not None:
            raise SlotAlreadyTakenError
        return await self.create(
            name=name,
            phone=phone,
            booking_date=booking_date,
            booking_time=booking_time,
            guests=guests,
        )

    async def get_booking(self, booking_id: int) -> Booking:
        """Бронь по id; если не найдена - BookingNotFoundError."""
        booking = await self.get(booking_id)
        if booking is None:
            raise BookingNotFoundError
        return booking

    async def cancel_booking(self, booking_id: int) -> Booking:
        """Мягкая отмена; если брони нет - BookingNotFoundError."""
        cancelled = await self.update(booking_id, status=BookingStatus.cancelled)
        if cancelled is None:
            raise BookingNotFoundError
        return cancelled
