import re
from datetime import UTC, date, datetime, time, timedelta

from pydantic import ConfigDict, Field, field_validator

from app.core.constants import FIRST_SLOT_HOUR, LAST_SLOT_HOUR, MAX_DAYS_AHEAD
from app.models import BookingStatus
from app.schemas.booking.base import BookingBaseSchema

PHONE_PATTERN = re.compile(r"^(?:7|8)\d{10}$")
NAME_PATTERN = re.compile(r"[^\W\d_]+(?:[ -][^\W\d_]+)*")


class PostBookingSchema(BookingBaseSchema):
    """Запрос на создание брони: общие поля + бизнес-валидация."""

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if not NAME_PATTERN.fullmatch(value):
            raise ValueError("Name must contain only letters, spaces and hyphens")
        return value

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        digits = re.sub(r"\D", "", value)
        if not PHONE_PATTERN.fullmatch(digits):
            raise ValueError("Enter a valid phone number: +7 or 8 followed by 10 digits")
        return "+7" + digits[1:]

    @field_validator("booking_date")
    @classmethod
    def validate_booking_date(cls, value: date) -> date:
        today = datetime.now(tz=UTC).date()
        if value < today:
            raise ValueError("Booking date cannot be in the past")
        if value > today + timedelta(days=MAX_DAYS_AHEAD):
            raise ValueError(
                f"Booking is available no more than {MAX_DAYS_AHEAD} days ahead"
            )
        return value

    @field_validator("booking_time")
    @classmethod
    def validate_booking_time(cls, value: time) -> time:
        if (
            value.minute != 0
            or value.second != 0
            or not FIRST_SLOT_HOUR <= value.hour <= LAST_SLOT_HOUR
        ):
            raise ValueError(
                f"Available slots: from {FIRST_SLOT_HOUR}:00 to {LAST_SLOT_HOUR}:00, every hour"
            )
        return value


class GetBooking(BookingBaseSchema):
    """Бронь в ответах API.

    Валидаторы создания сюда не наследуются намеренно: в ответах могут
    встречаться брони на уже прошедшие даты.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(examples=[1])
    status: BookingStatus = Field(examples=["active"])
