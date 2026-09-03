from datetime import date, time
from enum import Enum

from sqlalchemy import Date, Index, Integer, String, Time
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class BookingStatus(str, Enum):
    """Статусы брони."""

    active = "active"
    cancelled = "cancelled"


class Booking(Base):
    """Бронь столика в ресторане."""

    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))
    phone: Mapped[str] = mapped_column(String(20))
    booking_date: Mapped[date] = mapped_column(Date)
    booking_time: Mapped[time] = mapped_column(Time)
    guests: Mapped[int] = mapped_column(Integer)
    status: Mapped[BookingStatus] = mapped_column(
        SAEnum(BookingStatus, native_enum=False, length=16),
        default=BookingStatus.active,
    )

    __table_args__ = (
        # Частый запрос: поиск активной брони на конкретные дату и время (проверка занятости слота)
        Index("ix_bookings_date_time", "booking_date", "booking_time"),
    )
