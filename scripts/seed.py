"""Seeds the database with demo bookings.

Usage:
    uv run python scripts/seed.py            # skip if data already exists
    uv run python scripts/seed.py --force    # wipe bookings and reseed
"""

import asyncio
import sys
from datetime import date, time, timedelta

from app.core.database import async_session_maker
from app.models import BookingStatus
from app.services.repository.booking import BookingRepository

# (name, phone, days_from_today, slot, guests, status)
DEMO_BOOKINGS = [
    ("Ivan Petrov", "+79991234567", 1, time(12, 0), 2, BookingStatus.active),
    ("Anna Smirnova", "+79992345678", 1, time(19, 0), 4, BookingStatus.active),
    ("Petr Ivanov", "+79993456789", 2, time(13, 0), 3, BookingStatus.active),
    ("Maria Kozlova", "+79994567890", 2, time(20, 0), 6, BookingStatus.active),
    ("Oleg Sokolov", "+79995678901", 3, time(15, 0), 2, BookingStatus.cancelled),
    ("Daria Morozova", "+79996789012", 4, time(18, 0), 5, BookingStatus.active),
    ("Sergey Volkov", "+79997890123", 5, time(21, 0), 2, BookingStatus.active),
    ("Elena Pavlova", "+79998901234", 6, time(12, 0), 8, BookingStatus.cancelled),
]


async def seed(force: bool = False) -> None:
    async with async_session_maker() as session:
        repo = BookingRepository(session)

        if await repo.count() > 0:
            if not force:
                print(f"Bookings table already has {await repo.count()} rows. Use --force to reseed.")
                return
            deleted = await repo.delete_all()
            print(f"Wiped {deleted} existing bookings")

        today = date.today()
        for name, phone, days, slot, guests, status in DEMO_BOOKINGS:
            booking = await repo.create_booking(
                name=name,
                phone=phone,
                booking_date=today + timedelta(days=days),
                booking_time=slot,
                guests=guests,
            )
            if status == BookingStatus.cancelled:
                await repo.cancel_booking(booking.id)
            print(f"  id={booking.id}: {name} {booking.booking_date} {slot} -> {status.value}")

    print(f"Done: {len(DEMO_BOOKINGS)} bookings seeded")


if __name__ == "__main__":
    asyncio.run(seed(force="--force" in sys.argv))
