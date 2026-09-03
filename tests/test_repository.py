from datetime import date, time, timedelta

import pytest

from app.core.database import async_session_maker
from app.models import BookingStatus
from app.services.repository.booking import BookingRepository


@pytest.fixture
async def repo() -> BookingRepository:
    async with async_session_maker() as session:
        yield BookingRepository(session)


def make_data(**overrides) -> dict:
    data = {
        "name": "Иван Петров",
        "phone": "+79991234567",
        "booking_date": date.today() + timedelta(days=5),
        "booking_time": time(19, 0),
        "guests": 4,
    }
    data.update(overrides)
    return data


async def test_create_and_get(repo):
    booking = await repo.create(**make_data())
    assert booking.id is not None

    fetched = await repo.get(booking.id)
    assert fetched is not None
    assert fetched.name == "Иван Петров"


async def test_get_missing_returns_none(repo):
    assert await repo.get(999) is None


async def test_get_by_exists_count(repo):
    await repo.create(**make_data())

    found = await repo.get_by(phone="+79991234567")
    assert found is not None
    assert await repo.exists(phone="+79991234567") is True
    assert await repo.exists(phone="+70000000000") is False
    assert await repo.count() == 1


async def test_filter_by_date(repo):
    await repo.create(**make_data())
    await repo.create(**make_data(booking_date=date.today() + timedelta(days=6)))

    assert len(await repo.filter(booking_date=date.today() + timedelta(days=5))) == 1
    assert len(await repo.filter()) == 2


async def test_get_all_sorted(repo):
    await repo.create(
        **make_data(booking_date=date.today() + timedelta(days=6), booking_time=time(12, 0))
    )
    await repo.create(
        **make_data(booking_date=date.today() + timedelta(days=5), booking_time=time(20, 0))
    )

    bookings = await repo.get_all()
    assert [b.booking_date for b in bookings] == [
        date.today() + timedelta(days=5),
        date.today() + timedelta(days=6),
    ]


async def test_update_and_rowcount(repo):
    booking = await repo.create(**make_data())

    updated = await repo.update(booking.id, guests=6)
    assert updated is not None
    assert updated.guests == 6

    assert await repo.update_by({"id": booking.id}, guests=2) == 1
    assert await repo.update_by({"id": 999}, guests=2) == 0


async def test_update_or_create(repo):
    booking = await repo.create(**make_data())

    updated, created = await repo.update_or_create(defaults={"guests": 7}, id=booking.id)
    assert created is False
    assert updated.guests == 7

    defaults = make_data(guests=3)
    defaults.pop("name")  # имя задаётся фильтром, чтобы defaults его не перекрыли
    new_booking, created = await repo.update_or_create(defaults=defaults, name="Пётр")
    assert created is True
    assert new_booking.name == "Пётр"
    assert new_booking.guests == 3


async def test_delete_and_delete_all(repo):
    b1 = await repo.create(**make_data())
    await repo.create(**make_data(name="Пётр"))

    assert await repo.delete(b1.id) is True
    assert await repo.delete(b1.id) is False
    assert await repo.count() == 1

    assert await repo.delete_all() == 1
    assert await repo.count() == 0


async def test_slot_check_and_cancel(repo):
    booking = await repo.create(**make_data())

    assert await repo.get_active_by_slot(booking.booking_date, booking.booking_time) is not None

    cancelled = await repo.cancel_booking(booking.id)
    assert cancelled is not None
    assert cancelled.status == BookingStatus.cancelled
    assert await repo.get_active_by_slot(booking.booking_date, booking.booking_time) is None


async def test_bulk_operations(repo):
    await repo.bulk_create([make_data(name="Анна"), make_data(name="Пётр")])
    assert await repo.count() == 2

    ids = [b.id for b in await repo.get_all()]
    assert await repo.bulk_delete(ids) == 2
