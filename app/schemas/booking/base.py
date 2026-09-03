from datetime import date, time

from pydantic import BaseModel, Field


class BookingBaseSchema(BaseModel):
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
