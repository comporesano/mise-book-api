class BookingAPIError(Exception):
    """Базовое бизнес-исключение сервиса бронирования."""


class BookingNotFoundError(BookingAPIError):
    """Бронь с указанным id не найдена."""

    def __init__(self) -> None:
        super().__init__("Booking not found")


class SlotAlreadyTakenError(BookingAPIError):
    """Слот на выбранные дату и время уже занят активной бронью."""

    def __init__(self) -> None:
        super().__init__("Slot booked already")
