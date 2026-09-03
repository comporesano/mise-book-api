import re
from datetime import date, time, timedelta

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import BookingStatus

# Доступные слоты: с 12:00 до 22:00 включительно, шаг 1 час
FIRST_SLOT_HOUR = 12
LAST_SLOT_HOUR = 22
# Максимальная глубина бронирования, дней
MAX_DAYS_AHEAD = 90

PHONE_PATTERN = re.compile(r"^(?:7|8)\d{10}$")
NAME_PATTERN = re.compile(r"[^\W\d_]+(?:[ -][^\W\d_]+)*")


class BookingFields(BaseModel):
    """Общие поля брони: входные данные и данные в ответах."""

    name: str = Field(
        min_length=2,
        max_length=100,
        examples=["Иван Петров"],
        description="Имя гостя: минимум 2 символа, только буквы, пробелы и дефис",
    )
    phone: str = Field(
        examples=["+79991234567"],
        description="Российский номер: +7XXXXXXXXXX или 8XXXXXXXXXX",
    )
    booking_date: date = Field(examples=["2026-09-20"])
    booking_time: time = Field(examples=["19:00"])
    guests: int = Field(ge=1, le=12, examples=[4])


class BookingCreate(BookingFields):
    """Запрос на создание брони: общие поля + бизнес-валидация."""

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if not NAME_PATTERN.fullmatch(value):
            raise ValueError("Имя должно содержать только буквы, пробелы и дефис")
        return value

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        digits = re.sub(r"\D", "", value)
        if not PHONE_PATTERN.fullmatch(digits):
            raise ValueError("Введите корректный номер: +7 или 8, затем 10 цифр")
        return "+7" + digits[1:]  # канонический вид: 8XXXXXXXXXX -> +7XXXXXXXXXX

    @field_validator("booking_date")
    @classmethod
    def validate_booking_date(cls, value: date) -> date:
        today = date.today()
        if value < today:
            raise ValueError("Дата бронирования не может быть в прошлом")
        if value > today + timedelta(days=MAX_DAYS_AHEAD):
            raise ValueError(f"Бронирование доступно не далее чем за {MAX_DAYS_AHEAD} дней")
        return value

    @field_validator("booking_time")
    @classmethod
    def validate_booking_time(cls, value: time) -> time:
        if value.minute != 0 or value.second != 0 or not FIRST_SLOT_HOUR <= value.hour <= LAST_SLOT_HOUR:
            raise ValueError(f"Доступные слоты: с {FIRST_SLOT_HOUR}:00 до {LAST_SLOT_HOUR}:00 с шагом в 1 час")
        return value


class BookingOut(BookingFields):
    """Бронь в ответах API.

    Валидаторы создания сюда не наследуются намеренно: в ответах могут
    встречаться брони на уже прошедшие даты.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(examples=[1])
    status: BookingStatus = Field(examples=["active"])
